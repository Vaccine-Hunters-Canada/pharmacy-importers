import os
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
            session=session,
            discord_url=os.environ.get('DISCORD_PHARMACY_ON')
        )

        notifications = []
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

            vaccine_type = 1
            availability = False
            if availabilities.status == 200:
                body = await availabilities.json()
                for day in body['availability']:
                    if day['available'] == True:
                        availability = True
                        if "ZENECA" in location['name'].upper():
                            vaccine_type = 5
                        elif "PFIZER" in location['name'].upper():
                            vaccine_type = 4
                        elif "MODERNA" in location['name'].upper():
                            vaccine_type = 3
            # else:
            #     logging.info(availabilities.status)
            #     logging.info(await availabilities.text())
            
            location_data = {
                'line1': location['address'].strip(),
                'city': location['city'].strip(),
                'province': location['province'].strip(),
                'postcode': ''.join(location['postal'].split()),
                'name': location['name'].strip(),
                'url': 'https://www.pharmacyappointments.ca/appointment-select',
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
                if not state.get(location["id"]) and location_data["province"].upper() in ["ON", "ONTARIO"]:
                    notifications.append({
                        'name': name,
                        'url': f'https://portal.healthmyself.net/walmarton/guest/booking/form/8498c628-533b-41e8-a385-ea2a8214d6dc'
                    })
        
        await vhc.notify_discord('Sobeys Pharmacies', notifications)

        return json.dumps(newstate)
            