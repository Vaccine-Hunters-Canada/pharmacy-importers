import os
import csv
import json
import aiohttp
import datetime
from vhc import VHC
from bs4 import BeautifulSoup

import azure.functions as func


async def main(mytimer: func.TimerRequest, stateblob) -> str:
    telus_csv = open('TelusHealth/telus-health-locations.csv')
    telus_locations = csv.DictReader(telus_csv)

    state = {}
    newstate = {}
    if stateblob:
        state = json.load(stateblob)

    async with aiohttp.ClientSession() as session:

        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG_TELUS_HEALTH'),
            session=session,
            discord_url=os.environ.get('DISCORD_PHARMACY_ON')
        )

        notifications = []
        for location in telus_locations:

            if not location.get('postal'):
                continue

            url = f'https://pharmaconnect.ca/Appointment/{location["id"]}/Slots?serviceType=ImmunizationCovid'
            html = await session.get(url)
            page = BeautifulSoup(await html.text(), 'html.parser')
            dates = page.findAll('div', class_='b-days-selection appointment-availability__days-item')
            available = bool(dates)

            location_data = {
                'line1': location['address'].replace('<br>', ' ').strip(),
                'province': location['province'].strip(),
                'postcode': ''.join(location['postal'].split()),
                'name': location['name'].strip(),
                'phone': location['phone'].strip(),
                'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}/Book/ImmunizationCovid',
            }

            await vhc.add_availability(
                num_available=1 if available else 0,
                num_total=1 if available else 0,
                vaccine_type=1,
                location=location_data,
                external_key=location['id']
            )

            if available:
                name = f'{location_data["name"]} \n ({location_data["line1"]}) \n'
                newstate[location["id"]] = name
                if not state.get(location["id"]) and location_data["province"].upper() in ["ON", "ONTARIO"]:
                    notifications.append({
                        'name': name,
                        'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}/Book/ImmunizationCovid'
                    })
        
        await vhc.notify_discord('Telus Health Pharmacies', notifications)

        return json.dumps(newstate)