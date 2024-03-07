from flask import Flask, request
from flask_cors import CORS
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from os import environ
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
debug = environ.get('DEBUG', False)

SENTRY_DSN = environ.get('SENTRY_DSN')
if SENTRY_DSN is None:
    raise Exception('Please configure environment variable SENTRY_DSN')
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FlaskIntegration()]
)
sentry_sdk.set_tag("app", "fftt-les-tournois-cest-cool")

# Error handler for other exceptions
@app.errorhandler(Exception)
def handle_exception(error):
    sentry_sdk.capture_exception(error)
    if not hasattr(error, 'code'):
        error_code = 500
    else:
        error_code = error.code
    if not hasattr(error, 'description'):
        error_description = ''
    else:
        error_description = error.description
    return error_description, error_code

retry_strategy = Retry(
    total=3, #  Maximum number of retries
    backoff_factor=0.3, #  Exponential backoff factor
    status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
)

session = requests.session()
session.verify = False
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount('http://', adapter)
session.mount('https://', adapter)


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
        'order[startDate]': 'asc',
        'order[name]': 'asc'
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
    result = json.loads(response.content)
    return json.dumps(result), 200, {'Content-Type': 'application/json; charset=utf-8'}


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=debug)
