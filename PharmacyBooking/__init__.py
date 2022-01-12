import os
import re
import csv
import aiohttp
import urllib.parse
from vaccine_types import VaccineType
from vhc import VHC
from mockvhc import MockVHC
from bs4 import BeautifulSoup as soup

import azure.functions as func

async def main(mytimer: func.TimerRequest | None) -> None:
    return await run_importer(mytimer)

async def run_importer(mytimer: func.TimerRequest | None, dryrun: bool = False) -> None:
    pb_csv = open('PharmacyBooking/pharmacy-booking-locations.csv')
    pb_locations = csv.DictReader(pb_csv)

    async with aiohttp.ClientSession() as session:

        if dryrun == False:
            vhc = VHC(
                base_url=os.environ.get('BASE_URL'),
                api_key=os.environ.get('API_KEY'),
                org_id=os.environ.get('VHC_ORG_PHARMACY_BOOKING'),
                session=session
            )
        else:
            vhc = MockVHC()

        for location in pb_locations:
            url_dict = urllib.parse.parse_qs(urllib.parse.urlparse(location['url']).query)
            appointment_type = url_dict['appointmentType'][0]
            owner = url_dict['owner'][0]
            loc = url_dict['location'][0]

            # find the calendar code
            url_get = await session.get(location['url'])
            url_html = await url_get.text()
            html_soup = soup(url_html, 'html.parser')
            scripts= str(html_soup.find_all('script')[7])

            match = re.findall(r'typeToCalendars\[{0}] = \[\[(\d+).'.format(appointment_type), scripts)
            if len(match) > 0:
                calendar_code = match[0]

                # create post body
                post_data = {
                    'type': appointment_type,
                    'calendar': calendar_code,
                    'skip': 'true',
                    'options[qty]': 1,
                    'options[numDays]': 3,
                    'appointmentType': appointment_type
                }

                # create post url
                encoded_location = urllib.parse.urlencode({'location':loc})
                post_url = f'https://app.acuityscheduling.com/schedule.php?action=showCalendar&fulldate=1&owner={owner}&template=monthly&{encoded_location}'

                calendar_html = await session.post(post_url, data=post_data)

                data = await calendar_html.text()
                html = soup(data, 'html.parser')
                available = bool(html.findAll('td', class_='activeday'))

                location_data = {
                    'line1': location['address'],
                    'province': location['province'],
                    'postcode': ''.join(location['postal'].split()),
                    'name': location['name'],
                    'url': location['url']
                }

                await vhc.add_availability(
                    num_available=1 if available else 0,
                    num_total=1 if available else 0,
                    vaccine_type=VaccineType.UNKNOWN,
                    location=location_data,
                    external_key=location['id']
                )