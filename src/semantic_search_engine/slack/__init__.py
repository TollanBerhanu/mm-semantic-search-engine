import os
from peewee import SqliteDatabase
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH, SQLITE_PATH
from semantic_search_engine.chroma import ChromaSingleton

collection = ChromaSingleton().get_chroma_collection()

os.makedirs(TEMP_SLACK_DATA_PATH, exist_ok=True)

# get or create connection with SQLite database
db = SqliteDatabase(
   SQLITE_PATH + '/slack.db', pragmas={'journal_mode': 'wal', 'cache_size': 10000,'foreign_keys': 1}
)
print('Path to local db:', db.database)