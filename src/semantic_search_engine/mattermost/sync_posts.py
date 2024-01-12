import shelve
from semantic_search_engine.constants import LAST_SYNC_TIME_SHELVE, TOTAL_POSTS_SHELVE, SYNC_INTERVAL_SHELVE
from json import dumps as to_json
from datetime import datetime
from time import time, sleep
from semantic_search_engine.mattermost.mm_api import MattermostAPI
from semantic_search_engine.mattermost.mm_details import MMDetails
from semantic_search_engine.mattermost.mm_scheduler import MMScheduler
from semantic_search_engine.shelves import retrieve_one, store
from . import collection

sync_in_progress = False
sync_percentage = 0

class SyncPosts:

    def __init__(self, access_token, next_sync_scheduler) -> None:
        self.mm_api_request = MattermostAPI( access_token=access_token ).mm_api_request
        self.fetch_mm_details = MMDetails( access_token=access_token )
        self.next_sync_scheduler: MMScheduler = next_sync_scheduler

        self.sync_interval_in_seconds = retrieve_one( shelve_name=SYNC_INTERVAL_SHELVE, key='sync_interval' )
        # with shelve.open(SYNC_INTERVAL_SHELVE) as sync_interval:
        #     self.sync_interval_in_seconds = int(sync_interval[SYNC_INTERVAL_SHELVE])

        self.last_sync_time = retrieve_one( shelve_name=LAST_SYNC_TIME_SHELVE, key='last_sync_time' )
        # with shelve.open(LAST_SYNC_TIME_SHELVE) as last_sync_time:
        #     self.last_sync_time = int(last_sync_time[LAST_SYNC_TIME_SHELVE])

        self.prev_total_posts = retrieve_one( shelve_name=TOTAL_POSTS_SHELVE, key='total_posts' )
        # with shelve.open(TOTAL_POSTS_SHELVE) as total_posts:
        #     self.prev_total_posts = int(total_posts[TOTAL_POSTS_SHELVE])

    def get_all_channels(self,  *fields: [str]):
        all_channels = self.mm_api_request('/channels')
        channel_fields = [{field: res[field] for field in fields} for res in all_channels]
        return channel_fields

    def sync_latest_posts(self):
        print(f"\n {'*'*50} \n")

        global sync_in_progress
        sync_in_progress = True
        
        # Save the current time (before requesting the API)
        current_time = time()

        # Define 'since' in the request parameters. It will fetch all posts if this isn't defined
        post_params = {}
        if self.last_sync_time != 0 and self.prev_total_posts != 0:
            post_params = { 'since': int(self.last_sync_time * 1000) } # convert to milliseconds

        # Get all channels' data
        channels = self.get_all_channels('id', 'type', 'total_msg_count', 'display_name') 
        self.current_total_posts = sum( [int(channel['total_msg_count']) for channel in channels] )

        # Get the total number of posts since last sync
        self.total_posts = self.current_total_posts - self.prev_total_posts
        no_posts = 0

        for channel in channels:
            # 200 is the max number of posts per page
            # reset page to 0 for each channel
            post_params.update({'per_page': 10, 'page': 0})

            # previous_post_id is used to check if there are more pages of posts
            previous_post_id = '~'

            # Loop through all pages of posts for the channel
            while previous_post_id != '':
                # Get the server response for each page of posts
                posts_res = self.mm_api_request(
                    "/channels/" + channel["id"] + "/posts",
                    params=post_params
                )

                # Get the ids for all posts in the 'order' field and filter out each post_detail_fields we want for each post
                '''
                This is the schema for the response:
                    {
                        "order": [ ...list of post_ids... ],
                        "posts": {
                            ...."post_id_1": { ...1st post details... },
                                "post_id_2": { ...2nd post details... }...  }
                    }
                '''
                # Change the posts into a list of dictionaries with the above 'fields'
                posts = []
                fields = ['id', 'message', 'user_id', 'type', 'update_at', 'delete_at', 'channel_id']   # The required fields for each post
                for postId in posts_res['order']:
                    posts.append( { field: posts_res['posts'][postId][field] for field in fields } )
                no_posts += len(posts)
                # posts = [ { field: posts_res['posts'][postId][field] for field in fields } for postId in posts_res['order'] ]

                # Get the channel's access restriction (private / public)
                access = ''
                if channel["type"] == 'O':  access = 'pub'
                elif channel["type"] == 'P':  access = 'pri'
                else: continue
                
                # Remove deleted posts from chroma and filter out any irrelevant posts
                filtered_posts = self.delete_and_filter_posts(
                    posts=posts
                )
                
                # Upsert the filtered channel posts to Chroma
                self.upsert_mm_channel_posts(
                    posts=filtered_posts, 
                    access=access
                )

                # Update the page number and previous_post_id for the next page of posts
                post_params['page'] += 1
                previous_post_id = posts_res['prev_post_id']

                # yield with progress on every batch of posts fetched from MM's API
                if self.total_posts != 0:
                    # yield f'data: { round(no_posts / (total_posts-9), 3) }\n\n'
                    global sync_percentage
                    sync_percentage = abs( round(no_posts / (self.total_posts), 3) )
                    print('Sync Progress: ', sync_percentage )

            # yield to indicate channel is complete
            # yield f'data: { channel["display_name"] }\n\n'
        
        print('Total posts: ', self.total_posts)
        print('Total posts fetched: ', no_posts)

        sync_in_progress = False

        self.store_updated_values(
            updated_sync_time=current_time,
            updated_total_posts=self.current_total_posts
        )

        self.next_sync_scheduler.register_schedule(
            seconds=self.sync_interval_in_seconds,
            scheduler_function=self.sync_latest_posts
        )
    
    # --------- ######################### Helper Functions ######################### ---------
     
    def delete_and_filter_posts(self, posts):
        # TODO: filter out any stickers / emojis
        # TODO: replace user handles with their real names
        filtered_posts = []
        for post in posts:
            # print('POST ************** ', post)
            if post['delete_at'] > 0:
                collection.delete(ids=[post['id']])    # If the post has been deleted, also delete the message from Chroma
                print('Message deleted!')
            # Filter out any channel join and other type messages. Also filter out any empty string messages (only images, audio, ...)
            elif (post['type']=='' and post['message']): # If the 'type' is empty, that means it's a normal message (instead of 'system_join_channel')
                user_details = self.fetch_mm_details.get_user_details(post['user_id'], 'first_name', 'last_name', 'username')
                post['message'] = f"({ datetime.utcfromtimestamp(post['update_at'] / 1000).date() }) { user_details['name'] }: { post['message'] }"
                filtered_posts.append(post)

        return filtered_posts
    
    def upsert_mm_channel_posts(self, posts, access):
        if not posts:
            return
        try:
            user_ids=[post['user_id'] for post in posts]
            channel_ids=[post['channel_id'] for post in posts]
            '''
                {
                    "id" : "message_id",
                    "document" : "(date) User: message_text",
                    "metadata" : {
                        "source": "mm",
                        "access" : "pri / pub",
                        "channel_id" : "ch_sdfsa",
                        "user_id" : "usr_dfsdf",
                    }
                }
            '''
            collection.upsert(
                ids=[post['id'] for post in posts],
                documents=[post['message'] for post in posts],
                metadatas=[{**{'user_id': x}, 
                            **{'channel_id': y},
                            "access": access,
                            "source": 'mm'}  for x, y in zip(user_ids, channel_ids)]
            )
        except Exception as err:
            raise(f'Error while upserting Mattermost messages: {str(err)} ')

    def store_updated_values(self, updated_sync_time, updated_total_posts):
        # Update last_sync_time in shelve store
        store(
            shelve_name=LAST_SYNC_TIME_SHELVE,
            last_sync_time=updated_sync_time
        )
        # with shelve.open(LAST_SYNC_TIME_SHELVE) as db: # handles the closing of the shelve file automatically with context manager
        #     # Set the last fetch time to the current time for next api call
        #     db[LAST_SYNC_TIME_SHELVE] = current_time
        # # Update global last_sync_time
        self.last_sync_time = updated_sync_time

        store(
            shelve_name=TOTAL_POSTS_SHELVE,
            total_posts=updated_total_posts
        )
        # with shelve.open(TOTAL_POSTS_SHELVE) as db:
        #     db[TOTAL_POSTS_SHELVE] = total_posts + no_posts
        self.prev_total_posts = updated_total_posts

    
    # For real-time update of the fetch interval (without reinstantiating the 'Mattermost' Class)
    # @staticmethod
    # def update_sync_interval(self, interval):
    #     self.sync_interval_in_seconds = interval


def is_sync_inprogress():
    return sync_in_progress

def get_sync_percentage():
    return sync_percentage