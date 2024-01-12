import shelve
from flask import Response, Blueprint
from json import dumps as to_json
from semantic_search_engine.constants import SYNC_INTERVAL_SHELVE, LAST_SYNC_TIME_SHELVE, CHROMA_SHELVE
from routes.login_decorator import login_required
from semantic_search_engine.mattermost.sync_posts import is_sync_inprogress
from semantic_search_engine.shelves import retrieve_one
from . import mattermost

root_bp = Blueprint("root", __name__)

# ************************************************************** /ping

@root_bp.route('/ping', methods=['GET', 'HEAD'])
def ping():
    return Response(to_json('Hi'), status=200, mimetype='application/json')

# ************************************************************** /

@root_bp.route('/get', methods=['GET'])
@login_required(admin_only=True)
def root_route(loggedin_user):
    try:
        # res = {}
        # with shelve.open(SYNC_INTERVAL_SHELVE) as sync_interval_db:
        #     res['sync_interval'] = sync_interval_db[SYNC_INTERVAL_SHELVE]

        # with shelve.open(LAST_SYNC_TIME_SHELVE) as last_sync_time_db:
        #     res['last_sync_time'] = last_sync_time_db[LAST_SYNC_TIME_SHELVE] * 1000
        
        # with shelve.open( CHROMA_SHELVE ) as chroma_n_results_db:
        #     res['chroma_n_results'] =  chroma_n_results_db['chroma_n_results']
        #     res['max_chroma_distance'] =  chroma_n_results_db['max_chroma_distance']
            
        # res['is_syncing'] = mattermost.is_syncing()
        # res['in_progress'] = is_sync_inprogress()

        res = {
            'sync_interval' : retrieve_one( shelve_name=SYNC_INTERVAL_SHELVE, key='sync_interval' ),
            'last_sync_time' : float(retrieve_one( shelve_name=LAST_SYNC_TIME_SHELVE, key='last_sync_time' )) * 1000,
            'chroma_n_results' :  retrieve_one( shelve_name=CHROMA_SHELVE , key='chroma_n_results' ),
            'max_chroma_distance' :  retrieve_one( shelve_name=CHROMA_SHELVE, key='max_chroma_distance' ),
            'is_syncing' : mattermost.is_syncing(),
            'in_progress' : is_sync_inprogress()
        }

        return Response(to_json(res), status=200, mimetype='application/json')

    except Exception as err:
        return Response(to_json({
            'message': 'Something went wrong! Please restart the server.',
            'log': str( err )
            }), status=500, mimetype='application/json')
