from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRead
import os
import re
import json
import aiohttp
import logging
from mockvhc import MockVHC
from vaccine_types import VaccineType
from vhc import VHC

import azure.functions as func

vaccines = {
    'Pfizer 2nd Dose': { 'type': VaccineType.PFIZER, 'form': 5394, 'tags': [ '12+ Year Olds', 'Pfizer', '2nd Dose', '3rd Dose' ] },
    'Moderna 2nd Dose': { 'type': VaccineType.MODERNA, 'form': 5396, 'tags': [ '12+ Year Olds', 'Moderna', '2nd Dose', '3rd Dose' ] },
    'Pfizer 5-11 1st Dose': { 'type': VaccineType.PFIZER, 'form': 6460, 'tags': [ '5-11 Year Olds', 'Pfizer', '1st Dose' ] },
    'AstraZeneca 2nd Dose': { 'type': VaccineType.ASTRAZENECA, 'form': 5398, 'tags': [ '12+ Year Olds', 'AstraZeneca', '2nd Dose', '3rd Dose' ] },
}

location_availability = {}

async def main(mytimer: func.TimerRequest | None, stateblob: SupportsRead[str | bytes] | None) -> str:
    return await run_importer(mytimer, stateblob)

async def run_importer(mytimer: func.TimerRequest | None, stateblob: SupportsRead[str | bytes] | None, dryrun: bool = False) -> str:
    state = {}
    newstate = {}
    if stateblob:
        state = json.load(stateblob)

    notifications = []

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'authority': 'portal.healthmyself.net',
        'referer': 'https://portal.healthmyself.net/walmarton/forms/Dpd'
    }
    async with aiohttp.ClientSession(headers=headers) as session:

        if dryrun == False:
            vhc = VHC(
                base_url=os.environ.get('BASE_URL'),
                api_key=os.environ.get('API_KEY'),
                org_id=os.environ.get('VHC_ORG_WALMART'),
                session=session
            )
        else:
            vhc = MockVHC()

        # Create the session and get the session cookie
        await session.get('https://portal.healthmyself.net/walmarton/guest/booking/form/8498c628-533b-41e8-a385-ea2a8214d6dc')

        f = open('Walmart/walmart-locations.json')
        location_data = json.load(f)

        regex = re.compile(r'^(.+)(\([Moderna,Pfizer,AstraZeneca].+\))$', re.IGNORECASE)

        for location in location_data['locations']:
            location_id = location['loc_id']
            location_name = location['loc_name'].strip()
            external_key = f'walmart-{location_id}'

            if regex.search(location_name):
                location_name = regex.sub(r'\1', location_name).strip()

            tags: list[str] = []
            available = False
            vaccine_type = VaccineType.UNKNOWN

            for type in vaccines:
                vaccine = vaccines[type]
                logging.info(f'Getting {location_name} - {type} ...')
                form = vaccine.get('form')
                response = await session.get(f'https://portal.healthmyself.net/walmarton/guest/booking/{form}/schedules?locId={location_id}')
                if response.status == 200:
                    data = await response.json()
                    if data['data'][0]['available']:
                        tags.extend(vaccine.get('tags', []))
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
                'available': available,
                'type': vaccine_type,
                'tags': tags
            }

            if external_key in location_availability:
                location_availability[external_key]['tags'] = location_availability[external_key]['tags'].extend(tags)
            else:
                location_availability[external_key] = location_data

            location_availability[external_key]['tags'] = list(dict.fromkeys(location_availability[external_key]['tags']))

            total_tags = ', '.join(location_availability[external_key]['tags'])
            logging.info(f'Tags: {total_tags}')

        for lid in location_availability:
            loc = location_availability[lid]

            await vhc.add_availability(
                num_available=1 if loc.get('available', False) else 0,
                num_total=1 if loc.get('available', False) else 0,
                vaccine_type=loc.get('type', VaccineType.PFIZER),
                location=loc,
                external_key=lid
            )

            if loc.get('available', False):
                t = loc.get('tags', [])
                name = f'({", ".join(t)}) - {loc["name"]} - ({loc["city"]}, {loc["province"]})'
                newstate[lid] = name
                if not state.get(lid) and loc["province"].upper() in ["ON", "ONTARIO"]:
                    notifications.append({
                        'name': name,
                        'url': f'https://portal.healthmyself.net/walmarton/forms/Dpd'
                    })
        
        await vhc.notify_discord('Walmart Pharmacies', notifications, os.environ.get('DISCORD_PHARMACY_ON'))

        return json.dumps(newstate)
