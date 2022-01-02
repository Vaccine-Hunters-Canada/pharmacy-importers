import os
import csv
from os import name
import json
import aiohttp
import datetime
from vhc import VHC

import azure.functions as func

async def main(mytimer: func.TimerRequest, stateblob) -> str:
    pharmacies_csv = open('Calendly/pharmacies.csv')
    pharmacies_locations = csv.DictReader(pharmacies_csv)

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'
    }

    state = {}
    newstate = {}
    if stateblob:
        state = json.load(stateblob)

    start_date = datetime.datetime.utcnow()
    end_date = start_date + datetime.timedelta(days=60) # Use approximately 2 months

    start_date_formatted = start_date.strftime('%Y-%m-%d')
    end_date_formatted = end_date.strftime('%Y-%m-%d')

    async with aiohttp.ClientSession(headers=headers) as session:
        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG_CALENDLY'),
            session=session
        )

        for location in pharmacies_locations:
            address = location['address']
            city = location['city']
            province = location['province']
            postcode = location['postcode']
            id = location['id']
            url = location['url']
            name = location['name']

            availabilities = await session.get(
                f'https://calendly.com/api/booking/event_types/{id}/calendar/range?timezone=UTC&diagnostics=false&range_start={start_date_formatted}&range_end={end_date_formatted}'
            )

            if availabilities.status == 200:
                body = await availabilities.json()

                vaccine_type = 1 # Unknown vaccine type
                availability = False

                days = body['days']

                for day in days:
                    if day['status'] == 'available':
                        availability = True

                location_data = {
                    'line1': address,
                    'city': city,
                    'province': province,
                    'postcode': postcode,
                    'name': name,
                    'url': url,
                    'tags': ""
                }

                await vhc.add_availability(
                    num_available=1 if availability else 0,
                    num_total=1 if availability else 0,
                    vaccine_type=vaccine_type,
                    location=location_data,
                    external_key=location['id']
                )

                if availability:
                    name = f'{location["name"]} - ({location_data["city"]}, {location_data["province"]})'
                    newstate[location["id"]] = name

        return json.dumps(newstate)