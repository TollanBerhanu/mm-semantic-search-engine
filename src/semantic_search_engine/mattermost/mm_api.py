import os, requests, json, shelve
from semantic_search_engine.constants import MM_PAT_ID_SHELVE
from dotenv import load_dotenv
from semantic_search_engine.shelves import retrieve_one, store

load_dotenv()

class MattermostAPI:

    def __init__(self, access_token: str):
        self.mm_api_url = os.getenv("MM_API_URL")
        self.access_token = access_token


    def mm_api_request(self, route: str, params: dict={}, method: str='GET', data: dict={}):
        authHeader = "Bearer " + self.access_token # authenticate a user (through the MM API)

        try:
            res = requests.request(
                method=method,
                url=self.mm_api_url + route,
                params=params,
                data=json.dumps(data),
                headers={
                    "Content-type": "application/json; charset=UTF-8",
                    "Authorization": authHeader,
                },
            )
        except Exception as err:
            raise Exception(f"Request to Mattermost's API failed: ", err)
        
        # Guard against bad requests
        if res.status_code != requests.codes.ok:
            raise Exception(f"Request to '{route}' failed with status code: ", res.status_code)
            
        return res.json()

    def create_new_pat(self) -> str:
        pat_id = retrieve_one(
            shelve_name=MM_PAT_ID_SHELVE,
            key='personal_access_token_id'
        )
        # with shelve.open( MM_PAT_ID_SHELVE ) as pat_id:

        # if pat_id.get( MM_PAT_ID_SHELVE, False ):
        if pat_id:
            # Delete the prev pat
            res = self.mm_api_request(
                route='/users/tokens/revoke',
                method='POST',
                data={ 'token_id': pat_id }
            )
            if not res.get('status') == 'OK':
                print("Failed to delete previous personal access token!")

        # Create a new personal_access_token
        res = self.mm_api_request(
            route='/users/me/tokens',
            method='POST',
            data={ 'description': 'Mattermost Semantic Search' }
        )
        print(res)
        if not (res.get('id') or res.get('token')):
            raise Exception('Failed to create a new personal access token!')
        
        # Update the personal_access_token's id in shelve
        store(
            shelve_name=MM_PAT_ID_SHELVE,
            personal_access_token_id=res['id']
        )
        # pat_id[ MM_PAT_ID_SHELVE ] = res['id']

        return res['token']