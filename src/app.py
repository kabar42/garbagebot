from flask import Flask, redirect, request
from urllib.parse import urlencode, quote_plus
from textwrap import dedent
import os
import random
import requests
import string

app = Flask(__name__)


class Garbagebot(object):

    def __init__(self, app):
        self.app = app
        self.user_state = ""
        self.access_token = ""

        oauth_uri = 'https://api.twitch.tv/kraken/oauth2'
        client_id = '8s4hit7q1fl7o17xb1j2r6z2ed7zrvo'
        redirect_uri = 'http://localhost:8080/oauth'
        scopes = 'chat_login channel_editor'

        @self.app.route("/")
        def index():
            state_string =''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32))
            self.user_state = state_string

            payload = {'client_id': client_id,
                       'redirect_uri': redirect_uri,
                       'response_type': 'code',
                       'scope': scopes,
                       'state': state_string}
            request_uri = "{0}?{1}".format(oauth_uri+'/authorize', urlencode(payload, quote_via=quote_plus))
            return redirect(request_uri, code=302)

        @self.app.route("/oauth")
        def authorize():
            code = request.args.get('code')
            state = request.args.get('state')
            if state != self.user_state:
                return dedent("""<h1>State did not match</h1><br>
                              The session may have been interrupted""")

            client_info = self.read_client_info()

            payload = {'client_id': client_id,
                       'client_secret': client_info['client_secret'],
                       'code': code,
                       'grant_type': 'authorization_code',
                       'redirect_uri': redirect_uri,
                       'state': self.user_state}
            auth_res = requests.post(oauth_uri+'/token', data=payload)
            auth_data = auth_res.json()

            data_keys = auth_data.keys()
            if 'refresh_token' not in data_keys or \
               'access_token' not in data_keys:
                return "<h1>Error occurred while obtaining access token</h1><br>{0}".format(str(auth_res))

            self.access_token = auth_data['access_token']
            refresh_token = auth_data['refresh_token']

            # TODO: Use auth token to connect to chat
            return '<h1>Successfully obtained OAuth token</h1>'

    def run(self):
        self.app.run(host='0.0.0.0', port=8080)

    def read_client_info(self):
        client_info = {}
        cur_path = os.path.realpath(os.path.dirname(__file__))
        info_file = os.path.join(cur_path, 'client.info')
        with open(info_file, 'r') as f:
            entry = f.readline().strip().split('=')
            client_info[entry[0]] = entry[1]
        return client_info


if __name__ == "__main__":
    gb = Garbagebot(app)
    gb.run()
