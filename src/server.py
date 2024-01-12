import os
from flask import Flask, request
from flask_cors import CORS

from routes.root_route import root_bp
from routes.sync_route import sync_bp
from routes.search_route import search_bp
from routes.settings_route import settings_bp
from routes.slack_route import slack_bp

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:8065"}}, supports_credentials=True)
CORS(app=app,
     origins=os.getenv("MM_URL"),
     supports_credentials=True)

# Session config
# app.secret_key = os.getenv("APP_SECRET_KEY")  # Set the secret key for session management
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'
# app.config['SESSION_COOKIE_SECURE'] = True

app.register_blueprint(root_bp, url_prefix="/root")
app.register_blueprint(sync_bp, url_prefix="/sync")
app.register_blueprint(search_bp, url_prefix="/search")
app.register_blueprint(settings_bp, url_prefix="/settings")
app.register_blueprint(slack_bp, url_prefix="/slack")

import json

@app.route('/', methods=['GET'])
def ping():
    cookies = dict(request.cookies)
    print('hi', cookies)
    return json.dumps( dict(cookies) )

@app.route('/test', methods=['GET'])
def test():
    cookies = dict(request.cookies)
    print('test_cookies', cookies)
    return dict(cookies)

port_no = os.environ.get('PORT', 5555)

print(f"Server running on port {port_no}...")
if __name__ == '__main__':
    app.run(port=int(port_no), host="0.0.0.0")#, debug=True

