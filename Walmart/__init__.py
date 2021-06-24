import os
import re
import json
import aiohttp
import logging
from vhc import VHC

import azure.functions as func

vaccines = {
    'Pfizer': { 'type': 4, 'form': 5394 },
    'Moderna': { 'type': 3, 'form': 5396 },
    'AstraZeneca': { 'type': 5, 'form': 5398 }
}

async def main(mytimer: func.TimerRequest, stateblob) -> str:

    state = {}
    newstate = {}
    if stateblob:
        state = json.load(stateblob)

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'authority': 'portal.healthmyself.net',
        'referer': 'https://portal.healthmyself.net/walmarton/forms/Dpd'
    }
    async with aiohttp.ClientSession(headers=headers) as session:

        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG_WALMART'),
            session=session
        )

        # Create the session and get the session cookie
        await session.get('https://portal.healthmyself.net/walmarton/guest/booking/form/8498c628-533b-41e8-a385-ea2a8214d6dc')

        f = open('Walmart/walmart-locations.json')
        location_data = json.load(f)

        regex = re.compile(r'^(.+)(\([Moderna,Pfizer,AstraZeneca].+\))$', re.IGNORECASE)

        notifications = []
        for location in location_data['locations']:
            location_id = location['loc_id']
            location_name = location['loc_name'].strip()
            external_key = f'walmart-{location_id}'

            if regex.search(location_name):
                location_name = regex.sub(r'\1', location_name).strip()

            tags = []
            available = False
            vaccine_type = 1

            for type in vaccines:
                vaccine = vaccines[type]
                form = vaccine.get('form')
                response = await session.get(f'https://portal.healthmyself.net/walmarton/guest/booking/{form}/schedules?locId={location_id}')
                if response.status == 200:
                    data = await response.json()
                    if data['data'][0]['available']:
                        tags.append(type)
                        available = True
                        vaccine_type = vaccine.get('type')
            
            location_data = {
                'line1': location['address']['address'].strip(),
                'city': location['address']['city'].strip(),
                'province': location['address']['province'].strip(),
                'postcode': ''.join(location['address']['postal'].split()),
                'name': f'Walmart {location_name}',
                'phone': location['address']['phone'].strip(),
                'url': 'https://portal.healthmyself.net/walmarton/forms/Dpd',
            }

            if len(tags) > 0:
                location_data['tags'] = tags

            await vhc.add_availability(
                num_available=1 if available else 0,
                num_total=1 if available else 0,
                vaccine_type=vaccine_type,
                location=location_data,
                external_key=external_key
            )

            if available:
                name = f'({", ".join(tags)}) - {location_name} - ({location_data["city"]}, {location_data["province"]})'
                newstate[external_key] = name
                if not state.get(external_key) and location_data["province"].upper() in ["ON", "ONTARIO"]:
                    notifications.append({
                        'name': name,
                        'url': f'https://portal.healthmyself.net/walmarton/forms/Dpd'
                    })
        
        await vhc.notify_discord('Walmart Pharmacies', notifications, os.environ.get('DISCORD_PHARMACY_ON'))

        return json.dumps(newstate)
