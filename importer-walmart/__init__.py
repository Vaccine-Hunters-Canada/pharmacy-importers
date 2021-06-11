import os
import json
import time
import datetime
import aiohttp
import logging
from vhc import VHC

import azure.functions as func


async def main(mytimer: func.TimerRequest) -> None:

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'authority': 'portal.healthmyself.net',
        'referer': 'https://portal.healthmyself.net/walmarton/forms/Dpd'
    }
    async with aiohttp.ClientSession(headers=headers) as session:

        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG'),
            session=session
        )

        # Create the session and get the session cookie
        await session.get('https://portal.healthmyself.net/walmarton/guest/booking/form/8498c628-533b-41e8-a385-ea2a8214d6dc')

        f = open('importer-walmart/walmart-locations.json')
        location_data = json.load(f)

        for location in location_data['locations']:
            vaccine_type = 3
            location_id = location['loc_id']
            location_name = location['loc_name']
            external_key = f'walmart-{location_id}'

            response = await session.get(f'https://portal.healthmyself.net/walmarton/guest/booking/5395/schedules?locId={location_id}')
            if response.status != 200:
                vaccine_type = 4
                response = await session.get(f'https://portal.healthmyself.net/walmarton/guest/booking/5393/schedules?locId={location_id}')
            
            data = await response.json()
            available = False

            if response.status == 200 and data['data'][0]['available']:
                available = True

            va = {
                'numberAvailable': available,
                'numberTotal': available,
                'vaccine': vaccine_type,
                'inputType': 1,
                'tags': '',
                'organization': os.environ.get('VHC_ORG'),
                'line1': location['address']['address'],
                'city': location['address']['city'],
                'province': location['address']['province'],
                'postcode': ''.join(location['address']['postal'].split()),
                'name': f'Walmart {location_name}',
                'phone': location['address']['phone'],
                'active': 1,
                'url': 'https://portal.healthmyself.net/walmarton/guest/booking/form/8498c628-533b-41e8-a385-ea2a8214d6dc',
                'tagsL': '',
                'tagsA': '',
                'externalKey': external_key,
                'date': f'{datetime.datetime.now().date()}T00:00:00+00:00'
            }

            submission = await session.post(
                url=f"https://{os.environ.get('BASE_URL')}/api/v1/vaccine-availability/locations/key/{external_key}",
                json=va,
                headers={ 'authorization': f"Bearer {os.environ.get('API_KEY')}"}
            )

            if submission.status != 200:
                logging.error(await submission.text())

            logging.info(f'{available} - {location_name}')
