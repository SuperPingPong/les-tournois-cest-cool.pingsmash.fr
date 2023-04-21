from flask import Flask, request
from flask_cors import CORS

from os import environ
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxy = "https://mute-hill-43b6.cryptoshotgun.workers.dev/"
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
debug = environ.get('DEBUG', False)

session = requests.session()
session.verify = False
session.proxies = {"http": proxy}


@app.route("/api/search", methods=['POST', 'OPTIONS'])
def search():
    url = 'https://apiv2.fftt.com/api/tournament_requests'
    headers = {
        'referer': 'https://monclub.fftt.com/',
        'Content-Type': 'application/json; charset=utf-8'
    }
    params = {
        'page': 1,
        'itemsPerPage': 6,
        'order[startDate]': 'asc'
    }
    if debug:
        print(request.values)
        print(request.json)
    for item in request.json:
        key = item.get('name')
        value = item.get('value')
        if not value:
            continue
        if key == 'start-date':
            params['startDate[after]'] = f'{value}T00:00:00'
        if key == 'end-date':
            params['endDate[before]'] = f'{value}T00:00:00'
        if key in ['type[]', 'status[]']:
            if key not in params:
                params[key] = []
            params[key].append(value)
        if key in ['address.postalCode', 'address.addressLocality']:
            params[key] = value
        if key == 'page':
            params[key] = value

    if debug:
        print(params)
    response = session.get(url, headers=headers, params=params)
    return json.dumps(json.loads(response.content)), 200, {'Content-Type': 'application/json; charset=utf-8'}


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=debug)
