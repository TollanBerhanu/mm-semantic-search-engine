import shelve, os
from semantic_search_engine.constants import SHELVE_PATH
from semantic_search_engine.constants import *

def get_default_key(shelve_name: str) -> str:
    switcher = {
        LAST_SYNC_TIME_SHELVE : 'last_sync_time',
        SYNC_INTERVAL_SHELVE : 'sync_interval',
        TOTAL_POSTS_SHELVE : 'total_posts',
        MM_PAT_ID_SHELVE : 'personal_access_token_id'
    }
    return switcher.get(shelve_name, '')

def store(shelve_name: str, *args, **kwargs):
    try:
        with shelve.open( shelve_name ) as db:
            if len(args)==1:
                default_key = get_default_key(shelve_name=shelve_name)
                db[ default_key ] = args[0]

            elif kwargs:
                for key, value in kwargs.items():
                    db[ str(key) ] = value
    except:
        raise(f'Error while storing on shelve: "{shelve_name}"')

def retrieve_one(shelve_name: str, key: str = ''):
    try:
        with shelve.open( shelve_name ) as db:
            if key:
                return db.get(key, None)
            else:
                return db.get(shelve_name, None)
    except:
        raise(f'Error while retrieving from shelve: "{shelve_name}"')

def retrieve(shelve_name: str, *args):
    try:
        with shelve.open( shelve_name ) as db:
            value = []
            if args:
                for key in args:
                    value.append(db[ key ])
                return value[0] if len(value)==1 else value
            else:
                return dict( db )
    except:
        raise(f'Error while retrieving from shelve: "{shelve_name}"')

def create_default_shelve(shelve_name: str, default_value = None, **kwargs):
    # Create the shelve directory if it doesn't exist
    os.makedirs(SHELVE_PATH, exist_ok=True)

    with shelve.open( shelve_name ) as db:
        if kwargs:
            for key, value in kwargs.items():
                if not db.get( key, False ):
                    db[ str(key) ] = value

        else:
            if not db.get( shelve_name, False ):
                default_key = get_default_key(shelve_name=shelve_name)
                db[ default_key ] = default_value
