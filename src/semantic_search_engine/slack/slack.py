import os, json
from zipfile import ZipFile
from semantic_search_engine.slack.save import save_channel_messages, save_channels_data, save_users_data
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH
from . import db, collection

class Slack:

    def reset_slack(self) -> None:
        """ deletes all slack data from SQLite and Chroma
        """
        # Delete all data from SQL database
        Message.delete().execute()
        User.delete().execute()
        Channel.delete().execute()
        ChannelMember.delete().execute()

        # Delete all Chroma entries for Slack
        collection.delete(
            where={"source" : "sl"}
        )

    def upload_slack_data_zip(self, file_path: str) -> [dict]:
        """extract slack data from zip and store users and channels data
            then return the list of channel details for all channels
        Parameters
        ----------
        file_path : str
            the location of the zip file to extract
        Returns
        ----------
        [dict]
            a list of dict with the details for each channel
        """
        # Extract the zip file and store it in TEMP_SLACK_DATA_PATH
        with ZipFile(file_path, 'r') as zObject:
            zObject.extractall( path=TEMP_SLACK_DATA_PATH )
        
        # Get channels data from files and return them in a list
        file_names = ['channels.json', 'groups.json']   # Files that store public and private channels' data
        channel_details = []

        for file_name in file_names:
            public = file_name == 'channels.json'
            try:
                with open(file=os.path.join(TEMP_SLACK_DATA_PATH, file_name)) as json_file:
                    channels_json = json.load(json_file)
            except FileNotFoundError:
                print(f'"{ file_name }" doesn\'t exist in "{ TEMP_SLACK_DATA_PATH }"')
                continue

            for channel in channels_json:
                channel_details.append({
                    'id': channel['id'],
                    'name': channel['name'],
                    'date_created': channel['created'],
                    'no_members': len( channel['members'] ),
                    'access': 'public' if public else 'private',
                    'purpose': channel['purpose']['value']
                })
        return channel_details

    def store_slack_data(self, channel_specs: dict) -> None:
        """ loads the extracted file from directory and saves everything to Sqlite and Chroma
         Parameters
        ----------
        channel_specs : dict
            a dict containing the channel_ids along with the start and end dates
            it also contains store_all and store_none boolean values
        """
        # Get users data from the extracted file path and save to db
        save_users_data()

        # Get all channel_ids other than the ones where 'store_none'=True
        channel_ids = [ch_id for ch_id, spec in channel_specs.items() if not spec["store_none"]]

        # Get channels data from the extracted file path and save to db
        saved_channels = save_channels_data(
            channel_ids=channel_ids
        )

        # Get messages for each channel from the extracted file path and save to db
        # yield will respond with channel progress in real time 
        yield from save_channel_messages(
            collection=collection,
            saved_channels=saved_channels,
            channel_specs=channel_specs
        ) 

    @staticmethod
    def get_channel_details(channel_id: str):
        try:
            return Channel.select().where( Channel.channel_id==channel_id ).dicts().get()
        except:
            raise Exception(f'Failed to find "Channel" with id: {channel_id}')


    @staticmethod
    def get_user_details(user_id: str):
        try:
            return User.select().where( User.user_id==user_id ).dicts().get()
        except:
            raise Exception(f'Failed to find "User" with id: {user_id}')
            

    @staticmethod
    def get_message_details(message_id: str):
        try:
            return Message.select().where( Message.message_id==message_id ).dicts().get()
        except:
            raise Exception(f'Failed to find "Message" with id: {message_id}')
            

    @staticmethod
    def get_user_channels(user_email: str) -> [str]:
        member_channels = []
        try:
            with db.atomic():
                # Get the user's id corresponding to the email
                user_id = User.select().where( User.email==user_email ).dicts().get()['user_id']
                # Get the channel ids corrensponding to the user_id
                rows = ChannelMember.select(ChannelMember.channel_id).where( ChannelMember.user_id==user_id )
                for row in rows:
                    member_channels.append(row.channel_id)

            print(member_channels)
        except:
            print(f'Failed to find "User Channels" with email: "{user_email}"')
        
        return member_channels
