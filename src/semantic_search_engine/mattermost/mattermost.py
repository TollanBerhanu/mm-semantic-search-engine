import shelve
from time import time, sleep
from sched import scheduler

from semantic_search_engine.constants import DEFAULT_LAST_SYNC_TIME, DEFAULT_TOTAL_POSTS, LAST_SYNC_TIME_SHELVE, MM_PAT_ID_SHELVE, TOTAL_POSTS_SHELVE
from semantic_search_engine.mattermost.mm_api import MattermostAPI
from semantic_search_engine.mattermost.sync_posts import SyncPosts
from semantic_search_engine.mattermost.mm_scheduler import MMScheduler
from semantic_search_engine.shelves import store
from . import collection

class Mattermost:

    def __init__(self) -> None:
        self.next_sync_scheduler = MMScheduler()


    def start_sync(self, temp_access_token: str) -> None:

        # Get the last fetch time from shelve file store
        # with shelve.open(LAST_SYNC_TIME_SHELVE) as db: # handles the closing of the shelve file automatically with context manager
        #     if LAST_SYNC_TIME_SHELVE in db:
        #         last_sync_time = db[LAST_SYNC_TIME_SHELVE]
        #     else:
        #         last_sync_time = 0
        # last_sync_time = float( retrieve_one( shelve_name=LAST_SYNC_TIME_SHELVE, key='last_sync_time' ) )
        # if last_sync_time == 0: # No posts have been fetched before
        #     # self.stop_sync() # cancel any previously scheduled events
        #     print('Fetching all posts for the first time...')

        if self.is_syncing(): 
            print('Sync has already started!')
            return

        # Delete the previous and create a new personal access token for the Admin
        personal_access_token = MattermostAPI(
            access_token=temp_access_token
        ).create_new_pat()

        # Set the global MMApi instance with the new pat of the Admin
        sync_latest_posts = SyncPosts(
            access_token=personal_access_token,
            next_sync_scheduler=self.next_sync_scheduler
        ).sync_latest_posts

        # Add an event to the scheduler
        self.next_sync_scheduler.register_schedule(
            seconds=0,
            scheduler_function=sync_latest_posts
        )


    def stop_sync(self) -> None:
        try:
            self.next_sync_scheduler.cancel_all_schedules()
            print('Sync stopped!')
        except Exception as err:
            raise(f'Something went wrong while stopping sync {str(err)}')

    def is_syncing(self):
        return self.next_sync_scheduler.has_schedule()

    def reset_mattermost(self):
        self.stop_sync()
        try:
            collection.delete(
                where={"source" : "mm"}
            )
            store(
                shelve_name=LAST_SYNC_TIME_SHELVE,
                last_sync_time=DEFAULT_LAST_SYNC_TIME
            )
            # # Reset last_sync_time in shelve store
            # with shelve.open(LAST_SYNC_TIME_SHELVE) as last_sync_time:
            #     last_sync_time[LAST_SYNC_TIME_SHELVE] = DEFAULT_LAST_SYNC_TIME
            #     self.last_sync_time = DEFAULT_LAST_SYNC_TIME
            print('Last fetch time reset!')
                
            store(
                shelve_name=TOTAL_POSTS_SHELVE,
                total_posts=DEFAULT_TOTAL_POSTS
            )
            # with shelve.open(TOTAL_POSTS_SHELVE) as total_posts:
            #     total_posts[TOTAL_POSTS_SHELVE] = DEFAULT_TOTAL_POSTS
            #     self.prev_total_posts = DEFAULT_TOTAL_POSTS
            print('Total posts reset!')
        except:
            print('No Chroma Collection!')
