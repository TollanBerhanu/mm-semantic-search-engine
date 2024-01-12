import threading
from time import sleep, time
from flask import Blueprint, Response
from json import dumps as to_json
from . import mattermost
from semantic_search_engine.mattermost.sync_posts import get_sync_percentage, is_sync_inprogress
from routes.login_decorator import login_required

sync_bp = Blueprint('sync', __name__)


prev_is_syncing = False
prev_in_progress = False
prev_sync_progress = 0
timeout = 60 * 30 # The timeout to break the SSE event loop
   
# ************************************************************** /start_sync
    
@sync_bp.route('/start')#, methods=['GET'])
@login_required(admin_only=True)
def start_sync(loggedin_user):
    access_token = loggedin_user['auth_token']
    try:
        sync_thread = threading.Thread(target=mattermost.start_sync, args=(access_token,))
        sync_thread.start()

        sleep(1)    # Wait for the first sync to be scheduled
        return Response(to_json({
            'is_syncing': mattermost.is_syncing()
        }), status=200, mimetype='application/json')
        # print('starting sync...')
        # return Response(mattermost.start_sync(access_token), content_type='text/event-stream')
    
    except Exception as err:
        return Response(to_json({
            'message': 'Something went wrong while attempting to sync!',
            'log': str( err )
        }), status=500, mimetype='application/json')


# ************************************************************** /stop_sync
 
@sync_bp.route('/stop', methods=['GET'])
@login_required(admin_only=True)
def stop_sync(loggedin_user):
    try:
        mattermost.stop_sync()

        return Response(to_json({
            'is_syncing': mattermost.is_syncing()
        }), status=200, mimetype='application/json')
    
    except Exception as err:
        return Response(to_json({
            'message': 'Something went wrong while stopping the sync!',
            'log': str( err )
        }), status=500, mimetype='application/json')

# ************************************************************** Stream progress in real-time (SSE) **************************************************************

# ************************************************************** /is_inprogress
@sync_bp.route('/is_inprogress')
@login_required(admin_only=True)
def sync_in_progress(loggedin_user):
    def in_progress():
        start_time = time()
        while True:
            sync_in_progress = is_sync_inprogress()
            global prev_in_progress
            if sync_in_progress != prev_in_progress:
                prev_in_progress = sync_in_progress
                yield f"data: { sync_in_progress }\n\n"
            elif time() > start_time + timeout:
                break
            
            sleep(1)
    return Response(in_progress(), content_type='text/event-stream')

# ************************************************************** /is_started
@sync_bp.route('/is_started')
@login_required(admin_only=True)
def is_sync_started(loggedin_user):
    def is_started():
        start_time = time()
        while True:
            # yield f"data: {time.strftime('%H:%M:%S')}\n\n"
            global prev_is_syncing
            if mattermost.is_syncing() != prev_is_syncing:
                prev_is_syncing = mattermost.is_syncing()
                yield f"data: { mattermost.is_syncing() }\n\n"
            elif time() > start_time + timeout:
                break

            sleep(3)
    return Response(is_started(), content_type='text/event-stream')

# ************************************************************** /sync_percentage
@sync_bp.route('/sync_percentage')
@login_required(admin_only=True)
def get_sync_progress(loggedin_user):
    def sync_progress():
        start_time = time()
        while True:
            sync_percentage = get_sync_percentage()
            global prev_sync_progress
            if sync_percentage != prev_sync_progress:
                prev_sync_progress = sync_percentage
                yield f"data: { sync_percentage }\n\n"
            elif mattermost.is_syncing() and not is_sync_inprogress():
                break
            elif time() > start_time + timeout:
                break
            
            sleep(0.5)
    return Response(sync_progress(), content_type='text/event-stream')
