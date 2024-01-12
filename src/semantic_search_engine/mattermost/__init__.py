import shelve
import os
from semantic_search_engine.constants import *
from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine.shelves import create_default_shelve

collection = ChromaSingleton().get_chroma_collection()

# def __set_default_shelve(shelve_name: str, default_value):
#     with shelve.open( shelve_name ) as my_shelve:
#         if not my_shelve.get( shelve_name, False ):
#             my_shelve[ shelve_name ] = default_value

# # Create the shelve directory if it doesn't exist
# os.makedirs(SHELVE_PATH, exist_ok=True)

# Set default values for the following shelves if they don't exist

# Default sync_interval
create_default_shelve(
    shelve_name=SYNC_INTERVAL_SHELVE,
    sync_interval=DEFAULT_SYNC_INTERVAL 
)

# Default last_sync_time
create_default_shelve(
    shelve_name=LAST_SYNC_TIME_SHELVE,
    last_sync_time=DEFAULT_LAST_SYNC_TIME 
)

# Default total_posts
create_default_shelve(
    shelve_name=TOTAL_POSTS_SHELVE,
    total_posts=DEFAULT_TOTAL_POSTS
)

# Default personal_access_token_id
create_default_shelve(
    shelve_name=MM_PAT_ID_SHELVE,
    personal_access_token_id='' 
)