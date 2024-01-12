import shelve
from flask import Blueprint, request, Response
from json import dumps as to_json
from semantic_search_engine.constants import SYNC_INTERVAL_SHELVE, CHROMA_SHELVE
from routes.login_decorator import login_required
from semantic_search_engine.shelves import store, retrieve
from . import mattermost, slack

settings_bp = Blueprint("settings", __name__)

# ************************************************************** /set_sync_interval

@settings_bp.route('/sync_interval', methods=['GET', 'POST'])
@login_required(admin_only=True)
def set_sync_interval(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "sync_interval": "the time interval between syncs (in seconds)"
    } </h4></pre>'''

    elif request.method == 'POST':
        try:
            body = request.get_json()

            if body.get('sync_interval', False): 
                sync_interval = abs (float( body['sync_interval'] ))
                if sync_interval < 60 or sync_interval > (24 * 60 * 60):
                    return Response(to_json({ 'message': 'Sync interval must be between 1 minute and 24 hours!' }), status=400, mimetype='application/json')
                
                mattermost.stop_sync()
                sync_interval_db = store( SYNC_INTERVAL_SHELVE, sync_interval )
                # with shelve.open( SYNC_INTERVAL_SHELVE ) as sync_interval_db:
                #     sync_interval_db[SYNC_INTERVAL_SHELVE] = sync_interval
                    # SyncPosts.update_sync_interval(sync_interval_db[SYNC_INTERVAL_SHELVE])
                    # return Response(to_json( dict(sync_interval_db) ), status=200, mimetype='application/json')
                return Response(to_json( sync_interval_db ), status=200, mimetype='application/json')
            else:
                return Response(to_json({ 'message': 'Please provide a sync interval!' }), status=400, mimetype='application/json')
            
        except ValueError:
            return Response(to_json({ 'message': 'Invalid interval! Interval must be a number.' }), status=400, mimetype='application/json')
        except Exception as err:
            return Response(to_json({
                'message': 'Something went wrong while setting the fetch interval!',
                'log': str( err )
            }), status=500, mimetype='application/json')

# ************************************************************** /set_chroma_n_results

@settings_bp.route('/chroma', methods=['GET', 'POST'])
@login_required(admin_only=True)
def set_chroma_n_results(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "chroma_n_results": "the no. of messages given to the LLM as context",
        "max_chroma_distance": "the max. acceptable distance for to get results from chroma"
    } </h4></pre>'''

    elif request.method == 'POST':
        try:
            body = request.get_json()
            # with shelve.open( CHROMA_SHELVE ) as chroma_shelve:
            if body.get("chroma_n_results", False): 
                chroma_n_results = abs (int( body['chroma_n_results'] ))
                if chroma_n_results < 25 and chroma_n_results > 100:
                    return Response(to_json({ 'message': '\"chroma_n_results\" should be between 25 - 100!' }), status=400, mimetype='application/json')
                else:
                    store( shelve_name=CHROMA_SHELVE,
                          chroma_n_results=chroma_n_results )
                    # chroma_shelve['chroma_n_results'] = chroma_n_results

            if body.get("max_chroma_distance", False): 
                max_chroma_distance = abs (float( body['max_chroma_distance'] ))
                if max_chroma_distance < 0 and max_chroma_distance > 1:
                    return Response(to_json({ 'message': '\"max_chroma_distance\" should be between 0 - 1!' }), status=400, mimetype='application/json')
                else:
                    # chroma_shelve['max_chroma_distance'] = max_chroma_distance
                    store( shelve_name=CHROMA_SHELVE,
                          max_chroma_distance=max_chroma_distance )

            chroma_shelve = retrieve( CHROMA_SHELVE )
            return Response(to_json( dict(chroma_shelve) ), status=200, mimetype='application/json')

        except Exception as err:
            return Response(to_json({
                'message': 'Something went wrong while updating Chroma settings!',
                'log': str( err )
            }), status=500, mimetype='application/json')


# ************************************************************** /reset

@settings_bp.route('/reset', methods=['GET', 'POST'])
@login_required(admin_only=True)
def reset_all(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {
        "mattermost" : true | false,
        "slack" : true | false
    } </h4></pre>'''

    elif request.method == 'POST':
        try:
            body = request.get_json()

            if body.get("mattermost", False):
                mattermost.reset_mattermost()

            if body.get("slack", False):
                slack.reset_slack()
            
            return Response(to_json( 'Reset Successful!' ), status=200, mimetype='application/json')

        except Exception as err:
            return Response(to_json({
                'message': 'Something went wrong while resetting!',
                'log': str( err )
            }), status=500, mimetype='application/json')