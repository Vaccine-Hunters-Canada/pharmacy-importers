import os
import csv
import aiohttp
import datetime
from vhc import VHC

import azure.functions as func

VACCINE_DATA = 'WyJhM3A1bzAwMDAwMDAwb3VBQUEiLCJhM3A1bzAwMDAwMDAwdjJBQUEiLCJhM3A1bzAwMDAwMDAwdjdBQUEiLCJhM3A1bzAwMDAwMDAwVzdBQUkiLCJhM3A1bzAwMDAwMDAwVzJBQUkiLCJhM3A1bzAwMDAwMDAwVzNBQUkiLCJhM3A1bzAwMDAwMDAwVzVBQUkiLCJhM3A1bzAwMDAwMDAwV1dBQVkiLCJhM3A1bzAwMDAwMDAwZjRBQUEiLCJhM3A1bzAwMDAwMDAwZk9BQVEiLCJhM3A1bzAwMDAwMDAwZllBQVEiLCJhM3A1bzAwMDAwMDAwZ2xBQUEiLCJhM3A1bzAwMDAwMDAwbnJBQUEiLCJhM3A1bzAwMDAwMDAwb3pBQUEiLCJhM3A1bzAwMDAwMDAwcVJBQVEiLCJhM3A1bzAwMDAwMDAwZkpBQVEiLCJhM3A1bzAwMDAwMDAwcDRBQUEiXQ=='

async def main(mytimer: func.TimerRequest) -> None:
    sobeys_csv = open('Sobeys/sobeys-locations.csv')
    sobeys_locations = csv.DictReader(sobeys_csv)

    async with aiohttp.ClientSession() as session:

        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG_SOBEYS'),
            session=session
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
                'vaccineData': VACCINE_DATA
            }

            availabilities = await session.post(
                f'https://api.pharmacyappointments.ca/public/locations/{location["id"]}/availability',
                json=data
            )

            availability = False
            if availabilities.status == 200:
                body = await availabilities.json()
                for day in body['availability']:
                    if day['available'] == True:
                        availability = True
            
            location_data = {
                'line1': location['address'],
                'city': location['city'],
                'province': location['province'],
                'postcode': ''.join(location['postal'].split()),
                'name': location['name'],
                'url': 'https://www.pharmacyappointments.ca/appointment-select',
            }

            await vhc.add_availability(
                num_available=1 if availability else 0,
                num_total=1 if availability else 0,
                vaccine_type=1,
                location=location_data,
                external_key=location['id']
            )

            if availability and location_data['postcode'][0:2].upper() in ['K1', 'K2']:
                notifications.append({
                    'name': location['name'],
                    'url': f'https://portal.healthmyself.net/walmarton/guest/booking/form/8498c628-533b-41e8-a385-ea2a8214d6dc'
                })
        
        await vhc.notify_discord('Sobeys Pharmacies', notifications)
            