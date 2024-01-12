import os, requests
from functools import wraps
from flask import request, Response
from json import dumps as to_json

from dotenv import load_dotenv
load_dotenv()

mm_api_url = os.getenv("MM_API_URL")


# ************************************************************** /
def login_required(admin_only: bool):
    def inner_decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            cookies = dict(request.cookies)
            print('From decorator: ', cookies)
            auth_token = cookies.get('MMAUTHTOKEN')
            user_id = cookies.get('MMUSERID')
            print('Cookies: ', user_id, ' ***** ', auth_token)
            if not (auth_token and user_id):
                return Response(to_json({ 'message' : 'You must send requests with credentials enabled and be logged in!' }), status=400, mimetype='application/json')
            
            res = requests.get(
                f'{mm_api_url}/users/me',
                headers={ "Authorization": f"Bearer {cookies.get('MMAUTHTOKEN')}" },
            )
            if res.status_code != requests.codes.ok:
                return Response(to_json({ 'message' : 'Unauthorized! Your session might have expired.' }), status=401, mimetype='application/json')
            
            user_details = res.json()
            user_email = user_details.get('email', '')
            user_roles = user_details.get('roles', '').split(' ')

            #Check if an invalid response is returned from the API
            if not (user_email and user_roles):
                return Response(to_json({ 'message' : 'Invalid user data!' }), status=401, mimetype='application/json')

            #Check if the user has system_user role
            if not admin_only and 'system_user' not in user_roles:
                return Response(to_json({ 'message' : 'Unauthorized! You should be a Mattermost user' }), status=401, mimetype='application/json')
            
            # Check if the route requires admin privileges or not
            if admin_only and 'system_admin' not in user_roles:     
                return Response(to_json({ 'message' : 'Unauthorized! You don\'t have Admin privileges!' }), status=401, mimetype='application/json')
            loggedin_user = {
                'auth_token': auth_token,
                'user_info': {
                    'user_id': user_details.get('id', '') or user_id,
                    'name': f"{user_details.get('first_name', '')} {user_details.get('last_name', '')}".strip() or  user_details.get('username', ''),
                    'email': user_email
                }
            }
            return func(loggedin_user, *args, **kwargs)
        return decorated_function
    return inner_decorator

