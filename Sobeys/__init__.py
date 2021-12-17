import os
import re
import csv
import json
import aiohttp
import datetime
import logging
from vhc import VHC

import azure.functions as func

VACCINE_DATA = 'WyJhM3A1bzAwMDAwMDAweTFBQUEiXQ=='

async def main(mytimer: func.TimerRequest, stateblob) -> str:
    sobeys_csv = open('Sobeys/sobeys-locations.csv')
    sobeys_locations = csv.DictReader(sobeys_csv)

    p = re.compile(r'^(.+)\s-\s([A|P|M].+)$')

    headers = {
        'origin': 'https://www.pharmacyappointments.ca',
        'referer': 'https://www.pharmacyappointments.ca/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'
    }

    state = {}
    newstate = {}
    if stateblob:
        state = json.load(stateblob)

    async with aiohttp.ClientSession(headers=headers) as session:

        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG_SOBEYS'),
            session=session
        )

        notifications = {
            'ON': [],
            'AB': []
        }
        for location in sobeys_locations:
            today = datetime.datetime.utcnow()
            one_week = today + datetime.timedelta(days=7)

            data = {
                'doseNumber': 1,
                'startDate': str(today.date()),
                'endDate': str(one_week.date()),
                'url': 'https://www.pharmacyappointments.ca/appointment-select',
                'vaccineData': VACCINE_DATA,
                'timeZone': 'America/New_York'
            }

            availabilities = await session.post(
                f'https://api.pharmacyappointments.ca/public/locations/{location["id"]}/availability',
                json=data
            )

            tags = []
            vaccine_type = 1
            availability = False
            if availabilities.status == 200:
                body = await availabilities.json()
                for day in body['availability']:
                    if day['available'] == True:
                        availability = True
                        if "ZENECA" in location['name'].upper():
                            vaccine_type = 5
                            tags.append('AstraZeneca')
                        elif "PFIZER" in location['name'].upper():
                            vaccine_type = 4
                            tags.append('Pfizer')
                        elif "MODERNA" in location['name'].upper():
                            vaccine_type = 3
                            tags.append('Moderna')
                        
                        if "PEDI" in location['name'].upper() and "5-11" in location['name'].upper():
                            tags.extend(['5-11 Year Olds', '1st Dose'])
                        else:
                            tags.extend(['12+ Year Olds', '2nd Dose', '3rd Dose'])
            # else:
            #     logging.info(availabilities.status)
            #     logging.info(await availabilities.text())
            
            location_name = location['name'].strip()
            # m = p.match(location_name)
            # if m:
            #     location_name = m.group(1)

            location_data = {
                'line1': location['address'].strip(),
                'city': location['city'].strip(),
                'province': location['province'].strip(),
                'postcode': ''.join(location['postal'].split()),
                'name': location_name,
                'url': 'https://www.pharmacyappointments.ca/appointment-select',
                'tags': list(dict.fromkeys(tags))
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
                if not state.get(location["id"]):
                    if location_data["province"].upper() in ["ON", "ONTARIO"]:
                        notifications['ON'].append({
                            'name': name,
                            'url': f'https://www.pharmacyappointments.ca/'
                        })
                    elif location_data["province"].upper() in ["AB", "ALBERTA"]:
                        notifications['AB'].append({
                            'name': name,
                            'url': f'https://www.pharmacyappointments.ca/'
                        })
        
        await vhc.notify_discord('Sobeys Pharmacies', notifications['ON'], os.environ.get('DISCORD_PHARMACY_ON'))
        await vhc.notify_discord('Sobeys Pharmacies', notifications['AB'], os.environ.get('DISCORD_PHARMACY_AB'))

        return json.dumps(newstate)
            