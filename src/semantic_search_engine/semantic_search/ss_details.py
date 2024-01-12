from datetime import datetime
from semantic_search_engine.slack.slack import Slack as Sl
from semantic_search_engine.mattermost.mm_details import MMDetails

from os import getenv
from dotenv import load_dotenv
load_dotenv()

class SemanticSearchDetails:

    def __init__(self, access_token, user_info) -> None:
        self.mm_url = getenv("MM_URL")

        self.access_token = access_token
        # Initialze MMApi with the user's access_token
        self.mm_details = MMDetails(access_token=self.access_token)

        self.user_id = user_info['user_id']
        self.user_email = user_info['email']

    def get_user_channel_list(self) -> str:
        """Fetchs the list of channels of a user from Mattermost and Slack

        Returns
        -------
        str
            list of channel ids for Mattermost and Slack
        """
        # Get the channels list for the user from Mattermost's API
        mm_channels_list = self.mm_details.get_user_channels( user_id=self.user_id )
        # Get the channels list of Slack
        sl_channels_list = Sl.get_user_channels( user_email=self.user_email )

        # Concatenate the two lists to get the list of all channel_ids the user can access in Chroma
        return mm_channels_list + sl_channels_list

    def get_metadata_details(self, ids, metadatas, distances) -> [dict]:
        metadata_details = []

        for idx, metadata in enumerate(metadatas):
            
            schema = {
                "user_id":"",
                "user_name":"",
                "user_dm_link": "",
                "channel_name":"",
                "channel_link":"",
                "message":"",
                "message_link":"",
                "time":"",
                "source":"",
                "access":"",
                "score":""
            }
            if metadata['source']=='mm':
                try:
                    user_data = self.mm_details.get_user_details(
                        metadata['user_id'],
                        'first_name', 'last_name', 'username'
                        )
                    channel_data = self.mm_details.get_channel_details(
                        metadata['channel_id'],
                        'name', 'display_name', 'team_id'
                        )

                    post_data = self.mm_details.get_post_details(
                        ids[idx],
                        'id', 'message', 'update_at' # create_at
                        )
                    team_data = self.mm_details.get_team_details(
                        channel_data['team_id'],
                        'name'
                    )
                except: continue    # Skip context that lack any detail

                # Look for "api" from the right and cut out the url after that...  "http://localhost:8065/api/v4"  -->  "http://localhost:8065/"
                # mm_url = api_url[: api_url.rfind("api") ]
                
                link_url = f"{ self.mm_url }/{ team_data['name'] }"

                schema['user_id'] = metadata['user_id']                                                     # 0. user_id
                schema['user_name'] = user_data['name']                                                     # 1. user_name
                schema['user_dm_link'] = f"{ link_url }/messages/@{ user_data['username'] }"                # 2. user_dm_link

                schema['channel_name'] = channel_data['name']                                               # 3. channel_name 
                schema['channel_link'] = f"{ link_url }/channels/{ channel_data['name'] }"                  # 4. channel_link 
            
                schema['message'] = post_data['message']                                                    # 5. message
                schema['message_link'] = f"{ link_url }/pl/{ post_data['id'] }"                             # 6. message_link
                schema['time'] = (post_data['update_at']) / 1000                                            # 7. time

                schema['source'] = metadata['source']                                                       # 8. source (mm)
                schema['access'] = metadata['access']                                                       # 9. access
                schema['score'] = 1 - distances[idx]                                                        # 10. score
            
            elif metadata['source']=='sl':
                try:
                    sl_user_data = Sl.get_user_details( metadata['user_id'] )              
                    sl_channel_data = Sl.get_channel_details( metadata['channel_id'] )    
                    sl_message_data = Sl.get_message_details( ids[idx] )
                except: continue    # Skip context that lack any detail

                # schema['user_id'] = metadata['user_id']                                                   # 0. user_id            (not necessary for slack)
                schema['user_name'] = sl_user_data['real_name'] or sl_user_data['name']                     # 1. user_name
                # schema['user_dm_link'] = ...                                                              # 2. user_dm_link       (not applicable to slack)

                schema['channel_name'] = sl_channel_data['name']                                            # 3. channel_name 
                # schema['channel_link'] = ...                                                              # 4. channel_link       (not applicable to slack)
            
                schema['message'] = sl_message_data['text']                                                 # 5. message
                # schema['message_link'] = ...                                                              # 6. message_link       (not applicable to slack)
                ts = round( datetime.timestamp( sl_message_data['time'] ) , 3)
                schema['time'] = ts                                                                         # 7. time

                schema['source'] = metadata['source']                                                       # 8. source (sl)
                schema['access'] = metadata['access']                                                       # 9. access
                schema['score'] = 1 - distances[idx]                                                        # 10. score
                
            metadata_details.append(schema)
        
        return metadata_details


