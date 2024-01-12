import os
from dotenv import load_dotenv

load_dotenv()

# Chroma
DIR =  os.getcwd() #os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(DIR, 'chroma_db')
CHROMA_COLLECTION = "messages"
    # The following are only required if chroma is running as a hosted instance
CHROMA_HOST = os.environ.get("SS_CHROMA_DB_HOST") or "127.0.0.1"
CHROMA_PORT = os.environ.get("SS_CHROMA_DB_PORT") or 5555

# Slack Sqlite
SQLITE_PATH = os.path.join(DIR, 'sqlite')
TEMP_SLACK_DATA_PATH = os.path.join(SQLITE_PATH, 'temp/')

# LLM       # TODO: We should use our own instance of a hosted LLM
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_MODEL_NAME = os.environ.get("TOGETHER_MODEL_NAME") or "togethercomputer/llama-2-70b-chat"

# Default MM Sync Settings
DEFAULT_SYNC_INTERVAL = 15 * 60    # sync interval in seconds
DEFAULT_LAST_SYNC_TIME = 0
DEFAULT_TOTAL_POSTS = 0
# Default Chroma Settings
DEFAULT_CHROMA_N_RESULTS = 25
DEFAULT_MAX_CHROMA_DISTANCE = 0.6
# Default LLM Settings
DEFAULT_LLM_TEMPERATURE = 2
DEFAULT_LLM_MAX_TOKENS = 1024

# Shelve
SHELVE_PATH = os.path.join(DIR, 'shelve')

LAST_SYNC_TIME_SHELVE = os.path.join(SHELVE_PATH, "last_sync_time")
SYNC_INTERVAL_SHELVE = os.path.join(SHELVE_PATH, "sync_interval")
TOTAL_POSTS_SHELVE = os.path.join(SHELVE_PATH, "total_posts")
MM_PAT_ID_SHELVE = os.path.join(SHELVE_PATH, "personal_access_token_id")
CHROMA_SHELVE = os.path.join(SHELVE_PATH, "chroma_shelve")
