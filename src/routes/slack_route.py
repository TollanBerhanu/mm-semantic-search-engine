from os import remove, path
from flask import request, Response, Blueprint
from json import dumps as to_json
from routes.login_decorator import login_required
from semantic_search_engine.constants import TEMP_SLACK_DATA_PATH
from . import slack

slack_bp = Blueprint('slack', __name__)

slack_filter = {}

# ************************************************************** /upload_slack_zip
@slack_bp.route('/upload_zip', methods= ['GET', 'POST'])
@login_required(admin_only=True)
def save_slack_zip(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
        MultipartFormData    
            file = (Zip file containing slack export data)
    </h4></pre>'''

    elif request.method == 'POST':
        if "file" not in request.files:
            return Response(to_json({
                'message' : 'File Not Sent!'
            }), status=400, mimetype='application/json')
        try:
            file = request.files["file"]
            file_path = path.join(TEMP_SLACK_DATA_PATH, 'slack-export-data.zip')

            file.save(file_path)                                        # Save the zip file
            channel_details = slack.upload_slack_data_zip(file_path)    # Extract it and read the channel details
            remove(file_path)                                        # Delete the zip file

            return Response(to_json(channel_details), status=200, mimetype='application/json')
        
        except Exception as err:
            return Response(to_json({
                'message': 'Something went wrong while uploading the file!',
                'log': str( err )
            }), status=500, mimetype='application/json')


# ************************************************************** /store_slack_data

@slack_bp.route('/store_data', methods= ['GET', 'POST'])
@login_required(admin_only=True)
def store_data(loggedin_user):
    if request.method == 'GET':
        return '''<pre><h4> Send a POST request: <br>
    {   
        "channel_id" : {
            "store_all" : true | false,
            "store_none" : true | false,
            "start_date" : (start date in POSIX time),
            "end_date" : (end date in POSIX time)
        },
        ...
    } </h4></pre>'''

    elif request.method == 'POST':
    # if True:
        try:
            channel_specs = request.get_json()
            global slack_filter
            slack_filter = channel_specs

            # channel_specs = {'C05D1SE01B7': {'store_all': True, 'store_none': False, 'start_date': 1687165577, 'end_date': 1697805748.681}, 'C05D77W3N76': {'store_all': True, 'store_none': False, 'start_date': 1687165577, 'end_date': 1697805748.681}, 'C05D7863DRA': {'store_all': True, 'store_none': False, 'start_date': 1687165686, 'end_date': 1697805748.681}, 'C05ABCDE01': {'store_all': True, 'store_none': False, 'start_date': 1687166738, 'end_date': 1697805748.681}}
            # slack.store_slack_data(channel_specs=channel_specs)

            return Response(to_json( 'Filters saved!' ), status=200, mimetype='application/json')
            # return Response(slack.store_slack_data(channel_specs=channel_specs), content_type='text/event-stream')
        
        except Exception as err:
             return Response(to_json({
                'message': 'Something went wrong while saving the data!',
                'log': str( err )
            }), status=500, mimetype='application/json')


@slack_bp.route('/store_data_stream')
@login_required(admin_only=True)
def store_slack_data_stream(loggedin_user):
    try:
        # channel_specs = request.get_json()
        # channel_specs = {'C05D1SE01B7': {'store_all': True, 'store_none': False, 'start_date': 1687165577, 'end_date': 1697805748.681}, 'C05D77W3N76': {'store_all': True, 'store_none': False, 'start_date': 1687165577, 'end_date': 1697805748.681}, 'C05D7863DRA': {'store_all': True, 'store_none': False, 'start_date': 1687165686, 'end_date': 1697805748.681}, 'C05ABCDE01': {'store_all': True, 'store_none': False, 'start_date': 1687166738, 'end_date': 1697805748.681}}
        # slack.store_slack_data(channel_specs=channel_specs)
        #TODO: should return progress in real-time (channel by channel)
        global slack_filter

        # return Response(to_json( 'Slack data stored!' ), status=201, mimetype='application/json')
        return Response(slack.store_slack_data(channel_specs=slack_filter), content_type='text/event-stream')
    
    except Exception as err:
            return Response(to_json({
            'message': 'Something went wrong while saving the data!',
            'log': str( err )
        }), status=500, mimetype='application/json')
