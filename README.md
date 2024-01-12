# Semantic Search Engine

This repository houses an API designed for semantically searching exported Slack data. Follow these straightforward steps to run the Semantic Search Engine API.

### Getting Started
- **Clone the Repository:**
    ```bash
    git clone https://github.com/iCog-Labs-Dev/semantic-search-engine.git && \
    cd semantic-search-engine && \
    git checkout deploy-no-auth
    ```

- **Install requred packages:**
    ```bash
    pip install -r requirements.txt
    ```

- **Setup the environment variables:**
    ```bash
    cp .env.example .env
    ```

- **Start the Server:**
    <!-- 1. *Using Flask* -->
    ```bash
    python ./server.py
    ```
    <!-- 2. *Using Gunicorn*
    ```bash
    gunicorn -c gunicorn.conf.py -->
    ```

<!-- - **Or Use Docker (Download and Run):**
    ```bash
    docker pull tollan/semantic-search-engine
    docker run -p 8080:5555 tollan/semantic-search-engine
    ``` -->

### API Endpoints

- **Ping Server:**
    - `/` : Ping the server to check its status.

- **Get Server Settings:**
    - `/root/get` : Retrieve the server settings.

- **Semantic Search:**
    - `/search/*` : Search for messages semantically.

- **Settings:**
    - `/settings/sync_interval` : Set the sync interval to fetch new messages from Mattermost.
    - `/settings/chroma` : Set the number of results returned by Chroma or the maximum distance of the query to the messages in Chroma.
    - `/settings/reset` : Delete all Slack or Mattermost messages from Chroma DB.
    - `/settings/set_pat` : Set the personal access token for the admin user.

- **Slack Data Handling:**
    - `/slack/upload_zip` : Upload a zipped file of exported Slack messages.
    - `/slack/store_data` : Extract and store messages from the uploaded Slack zip file.
    - `/slack/store_data_stream` : Send progress of storing all Slack messages.

- **Sync Process:**
    - `/sync/start` : Start syncing Mattermost messages to Chroma.
    - `/sync/stop` : Stop the syncing process.
    - `/sync/sync_percentage` : Get the progress of the ongoing sync process.
    - `/sync/is_started` : Check whether sync has already started.
    - `/sync/is_inprogress` : Check whether the sync process is running or not.
