import os, json, re
from datetime import datetime
import time

from flask import Response
from semantic_search_engine.slack.models import User, Channel, ChannelMember, Message
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH
from peewee import chunked
from . import db


def save_users_data() -> None:

    """reads users' relevant info from users.json and save it to Sqlite db
    """
    # Create a User table if it doesn't exist
    User.create_table()
    
    with open(os.path.join(TEMP_SLACK_DATA_PATH, 'users.json')) as json_file:
        users_json = json.load(json_file) 
    users = []
    for user in users_json:
        user_data = {
            'user_id': user['id'],
            'name': user['name'],
            'real_name': user['profile']['real_name'],
            'email': user['profile']['email'],
            'is_bot': user['is_bot'],
            'avatar': user['profile']['image_192']
        }
        users.append(user_data)

    with db.atomic():
        # User.bulk_create(users, batch_size=100)
        for batch in chunked(users, 100):
            User.insert_many(batch).on_conflict_replace().execute()

def save_channels_data(channel_ids: [str]) -> [dict]:
    """reads channels' relevant info from channels.json and save it to Sqlite db
    """
    # Create 'Channel' and 'ChannelMember' tables if they don't exist
    Channel.create_table()
    ChannelMember.create_table()

    file_names = ['channels.json', 'groups.json']   # Files that hold data for public and private channels
    saved_channels = []

    for file_name in file_names:
        access = 'pub' if file_name == 'channels.json' else 'pri'
        try:
            with open(file=os.path.join(TEMP_SLACK_DATA_PATH, file_name)) as json_file:
                channels_json = json.load(json_file) 
        except FileNotFoundError:
            print(f'"{ file_name }" doesn\'t exist in "{ TEMP_SLACK_DATA_PATH }"')
            continue

        channels = []
        channel_members = []
        for channel in channels_json:
            # Check if the channel_id is in the list of selected channels
            if channel['id'] not in channel_ids:
                continue

            channel_data = {
                'channel_id': channel['id'],
                'name': channel['name'],
                'access': access,
                'purpose': channel['purpose']['value']
            }
            channels.append(channel_data)
            
            for member_user_id in channel['members']:
                channel_member =  {
                    'channel_id': channel['id'],
                    'user_id': member_user_id
                }
                channel_members.append(channel_member)

            saved_channels.append({
                'id': channel['id'],
                'name': channel['name'],
                'access': access
            })

        with db.atomic():
            for batch in chunked(channels, 100):
                Channel.insert_many(batch).on_conflict_replace().execute()

            for batch in chunked(channel_members, 100):
                ChannelMember.insert_many(batch).on_conflict_replace().execute()

    return saved_channels


def save_channel_messages(collection, saved_channels: [dict], channel_specs: [dict]) -> None:
    """ Reads messages from a single channel file and saves the relevant info to Sqlite and Chroma.
    """
    # Create a Message table if it doesn't exist
    Message.create_table()

    for channel in saved_channels:
    
        # Get the directory where the channel data is stored
        channel_folder = os.path.join(TEMP_SLACK_DATA_PATH, channel['name'])
        channel_id = channel['id']
        spec = channel_specs[channel_id]

        if spec['store_none']:  # This is shouldn't happen because the channels are already filtered in 'slack.py'
            continue
        elif spec['store_all']:
            start_date = datetime.utcfromtimestamp(0).date()
            end_date = datetime.now().date()
        else:
            start_date = datetime.utcfromtimestamp(float(spec['start_date'])).date()
            end_date = datetime.utcfromtimestamp(float(spec['end_date'])).date()
            if start_date >= end_date: 
                print('Start date cannot be larger that end date!')
                continue

        # Get all files in the channel's folder (each file correspond to daily messages)
        all_files = os.listdir(channel_folder)
        no_files = len(all_files)

        for idx, file_name in enumerate(all_files):

            # Get the date from the filename and check whether it's in the range provided
            date_str = file_name.split('.json')[0]  # The files are stored as YYYY-mm-dd.json
            file_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Don't save the files that are out of the specified date range
            if start_date > file_date or end_date < file_date:
                continue

            # Read the content of the file (all messages sent in that channel in one day)
            with open(file=channel_folder + '/' + file_name) as json_file:
                messages_json = json.load(json_file)

            messages = []
            ids = []
            documents = []
            metadatas = []

            for message in messages_json:
                # subtype == channel_join is a system message that tells a users has joined a channel, not really necessary
                # Check if 'client_msg_id' and 'text' exists/aren't empty in the json file, or else return False
                if not (message.get("client_msg_id", False) and message.get("text", False)): 
                    continue
                
                message_text = replace_slack_handles( message['text'] ) 
                date_time = datetime.utcfromtimestamp( float(message['ts']) )

                message_data = {
                    'message_id': message['client_msg_id'],
                    'user_id': message['user'],
                    'channel_id': channel_id,
                    'text': message_text,
                    'time': date_time
                }
                messages.append(message_data)

                ids.append(message['client_msg_id'])
                # Each message is embedded with the name of the user and the date / time
                documents.append(f"({date_time.date()}) { message['user_profile']['real_name'] }: { message_text }")
                metadatas.append({
                    "user_id" : message['user'],
                    "channel_id" : channel_id,
                    "access" : channel['access'],
                    "source" : 'sl',
                })

            print(f'Saving channel "{ channel["name"] }" ...', end=' ')
            if messages:
                # Use insert_many with on_conflict_replace() to insert new messages and update existing ones
                with db.atomic():
                    for batch in chunked(messages, 100):
                        Message.insert_many(batch).on_conflict_replace().execute()

                # Upsert messages to chroma
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print('Done!')
            else: print('The channel is empty!')

            yield f'data: { json.dumps({ channel_id: (idx+1)/ no_files }) }\n\n'


# Hello <@user_id> -->  Hello user_name
def replace_slack_handles(message: str) -> str:
    # Define a regular expression pattern to match <@ ... >
    pattern = r'<@(\w+)>'   # r"\<@([a-zA-Z0-9]+)\>"

    def replace_match(match):
        # Extract the user_id from the matched pattern
        user_id = match.group(1)
        # Lookup the user_id from the slack database and use the real_name, username or the original pattern
        try:
            user = User.select().where( User.user_id==user_id ).dicts().get()
            replacement = user['real_name'] or user['name'] or f'<@{user_id}>'
        except: 
            replacement = f'<@{user_id}>'
        # Use the user_id to look up the replacement in the dictionary; if not found, use the original pattern
        return replacement

    # Use re.sub to search for the pattern and replace it with the result of the replace_match function
    output_string = re.sub(pattern, replace_match, message)
    return output_string