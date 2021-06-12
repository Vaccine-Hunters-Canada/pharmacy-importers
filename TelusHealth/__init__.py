import os
import csv
import aiohttp
import datetime
from vhc import VHC
from bs4 import BeautifulSoup

import azure.functions as func


async def main(mytimer: func.TimerRequest) -> None:
    telus_csv = open('TelusHealth/telus-health-locations.csv')
    telus_locations = csv.DictReader(telus_csv)

    async with aiohttp.ClientSession() as session:

        vhc = VHC(
            base_url=os.environ.get('BASE_URL'),
            api_key=os.environ.get('API_KEY'),
            org_id=os.environ.get('VHC_ORG_TELUS_HEALTH'),
            session=session
        )

        for location in telus_locations:

            if not location.get('postal'):
                continue

            url = f'https://pharmaconnect.ca/Appointment/{location["id"]}/Slots?serviceType=ImmunizationCovid'
            html = await session.get(url)
            page = BeautifulSoup(await html.text(), 'html.parser')
            dates = page.findAll('div', class_='b-days-selection appointment-availability__days-item')
            available = bool(dates)

            location_data = {
                'line1': location['address'],
                'province': location['province'],
                'postcode': ''.join(location['postal'].split()),
                'name': location['name'],
                'phone': location['phone'],
                'url': url,
            }

            await vhc.add_availability(
                num_available=1 if available else 0,
                num_total=1 if available else 0,
                vaccine_type=1,
                location=location_data,
                external_key=location['id']
            )