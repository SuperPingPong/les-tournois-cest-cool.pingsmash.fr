from datetime import datetime
import json
from os import environ
import hashlib
import logging
import math
import time

import googlemaps

import requests
from urllib.parse import urlparse, quote, urlunparse, urlencode

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

session = requests.session()
session.headers = {
    'Content-type': 'application/json'
}

PAGE_SIZE=6
URL = 'http://api:5000/api/search'

#  MAX_DISTANCE = 300 * 1000 # in meters
MAX_DISTANCE = 100000 * 1000 # in meters

GMAP_API_KEY=environ.get('GMAP_API_KEY')
if GMAP_API_KEY is None:
    raise Exception('Please set environment var GMAP_API_KEY')
ORIGIN='44 Mail le Corbusier, 77185 Lognes'
gmaps = googlemaps.Client(key=GMAP_API_KEY)

WHAPI_TOKEN=environ.get('WHAPI_TOKEN')
if WHAPI_TOKEN is None:
    raise Exception('Please set environment var WHAPI_TOKEN')

def get_response(page: int):
    now = datetime.now()
    start_date = now.strftime('%Y-%m-%d')
    end_date = now.replace(year=now.year + 1).strftime('%Y-%m-%d')

    data = [
        {"name": "start-date", "value": start_date},
        {"name": "end-date", "value": end_date},
        {"name": "status[]", "value": "1"},
        {"name": "type[]", "value": "I"},
        {"name": "type[]", "value": "A"},
        {"name": "type[]", "value": "B"},
    ]
    return session.post(
        URL,
        json=data + [{"name": "page", "value": str(page)}]
    ).json()

def create_maps_link(origin, destination, mode="driving"):
    base_url = "https://www.google.com/maps"
    params = {
        "saddr": origin,
        "daddr": destination,
        "dirflg": mode
    }
    maps_link = f"{base_url}?{urlencode(params)}"

    directions_result = gmaps.directions(origin, destination, mode=mode)
    if directions_result:
        start_location = directions_result[0]["legs"][0]["start_location"]
        end_location = directions_result[0]["legs"][0]["end_location"]
        maps_link = f"https://www.google.com/maps/dir/?api=1&origin={start_location['lat']},{start_location['lng']}&destination={end_location['lat']},{end_location['lng']}&travelmode={mode}"
        return maps_link
    else:
        return ""

def create_fingerprint(title, club_name, destination, start_date, end_date, contact, email):
    data_to_hash = f"{title}{club_name}{destination}{start_date}{end_date}{contact}{email}"
    fingerprint = hashlib.sha256(data_to_hash.encode()).hexdigest()
    return fingerprint

def compute_tournaments():
    RESPONSES = []

    page = 1
    response = get_response(page=page)
    RESPONSES.append(response)

    total_items = response['hydra:totalItems']
    if total_items > page * PAGE_SIZE:
        total_pages = math.ceil(total_items / PAGE_SIZE)
    else:
        total_pages = 1

    for page in range(2, total_pages + 1):
        response = get_response(page=page)
        RESPONSES.append(response)

    RESPONSES_TO_COMPUTE = []
    for response in RESPONSES:
        members=response['hydra:member']
        RESPONSES_TO_COMPUTE += members

    RESPONSES_TO_COMPUTE = sorted(RESPONSES_TO_COMPUTE, key=lambda x: x.get('startDate', ''))

    for member in RESPONSES_TO_COMPUTE:

        destination = ''
        address = member["address"]
        if address.get("streetAddress") is not None:
            destination += address["streetAddress"] + ', '
        if address.get("postalCode") is not None:
            destination += address["postalCode"] + ', '
        if address.get("addressLocality") is not None:
            destination += address["addressLocality"] + ', '
        if address.get("addressRegion") is not None:
            destination += address["addressRegion"]
        destination = destination.rstrip(', ').strip()

        title = member['name']
        club_name = member['club']['name']

        start_date = member['startDate']
        formatted_start_date = f"{start_date[:4]}-{start_date[5:7]}-{start_date[8:10]}"
        end_date = member['endDate']
        formatted_end_date = f"{end_date[:4]}-{end_date[5:7]}-{end_date[8:10]}"

        #  date_range = f'Dates: {formatted_start_date} - {formatted_end_date}'

        contact = f'Organisateur: {member["contacts"][0]["givenName"]} {member["contacts"][0]["familyName"]}'
        email = f'Contact: {member["contacts"][0]["email"]}'

        rule = member['rules']['url']
        url_components = urlparse(rule)
        encoded_path = quote(url_components.path)
        encoded_query = quote(url_components.query)
        rule = urlunparse((url_components.scheme, url_components.netloc, encoded_path, url_components.params, encoded_query, url_components.fragment))

        fingerprint = create_fingerprint(title, club_name, destination, start_date, end_date, contact, email)
        if fingerprint in RESULT:
            continue

        directions_result = gmaps.directions(ORIGIN, destination, mode="driving")
        driving_distance_km = directions_result[0]['legs'][0]['distance']['text'].replace(' ', '')

        driving_distance_m_value = directions_result[0]['legs'][0]['distance']['value']
        if driving_distance_m_value > MAX_DISTANCE:
            RESULT[fingerprint] = None
            continue

        maps_url = create_maps_link(ORIGIN, destination)

        result = [
            f"🏆 {title}",
            f"🏠 {club_name}",
            f"📍 {destination}",
            f"📅 {formatted_start_date} - {formatted_end_date}",
            #  f"📅 {date_range}"
            f"👤 {contact}",
            f"✉️ {email}",
            f"📜 {rule}",
            f"🚗 {driving_distance_km}",
            f"🗺️ {maps_url}",
            ''
        ]
        #  print('\n'.join(result))

        RESULT[fingerprint] = result
        time.sleep(0.5)

def send_notification(message: str):
    url='https://gate.whapi.cloud/messages/text'
    group = '120363206509427829@g.us'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {WHAPI_TOKEN}'
    }
    data =  {
        'typing_time': 0,
        'to': group,
        'body': message
    }
    return session.post(url, headers=headers, json=data)


RESULT={}
if __name__ == '__main__':

    # init
    logging.info('🏓 Init compute available tournaments')
    compute_tournaments()
    logging.info('✅ Init done')
    logging.info('---')

    while True:
        CURRENT_TOURNAMENT_FINGERPRINTS = set(RESULT.keys())
        # Update fingerprints of tournaments
        compute_tournaments()
        NEW_TOURNAMENT_FINGERPRINTS = set(RESULT.keys())

        # Send notifications for new tournaments
        FINGERPRINTS_TO_COMPUTE = list(NEW_TOURNAMENT_FINGERPRINTS - CURRENT_TOURNAMENT_FINGERPRINTS)
        for fingerprint in FINGERPRINTS_TO_COMPUTE:
            result = RESULT[fingerprint]
            if result is None:
                continue
            result_to_display='\n'.join(result)
            message = '🤖 Nouveau tournoi détecté 🤖\n\n' + result_to_display
            logging.info(message)
            logging.info('---')
            send_notification(message)

        time.sleep(10 * 60)
