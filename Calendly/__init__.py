#import os
#import re
#import csv
#import json
import aiohttp
import datetime
#import logging
import asyncio
import sys
import pytz
#from vhc import VHC

#import azure.functions as func

async def main():
#async def main(mytimer: func.TimerRequest, stateblob) -> str:
    id = 'AGA35VEWK3SLXFOR'

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'
    }

    start_date = datetime.datetime.now(pytz.timezone("America/New_York")) # Get current time in Eastern time
    print(start_date)
    end_date = start_date + datetime.timedelta(days=60) # Use approximately 2 months

    async with aiohttp.ClientSession(headers=headers) as session:
        #vhc = VHC(
        #    base_url=os.environ.get('BASE_URL'),
        #    api_key=os.environ.get('API_KEY'),
        #    org_id=os.environ.get('VHC_ORG_CALENDLY'),
        #    session=session
        #)

        availabilities = await session.get(
            f'https://calendly.com/api/booking/event_types/{id}/calendar/range?timezone=America%2FNew_York&diagnostics=false&range_start=2021-12-26&range_end=2022-02-20'
        )

        if availabilities.status == 200:
            body = await availabilities.json()

            #print(body)

            vaccine_type = 1
            availability = False

            days = body['days']

            for day in days:
                if day['status'] == 'available':
                    availability = True

            location_data = {
                'line1': "test",
                'city': "test",
                'province': "test",
                'postcode': "test",
                'name': "test",
                'url': "test",
                'tags': "test"
            }

            # await vhc.add_availability(
            #     num_available=1 if availability else 0,
            #     num_total=1 if availability else 0,
            #     vaccine_type=vaccine_type,
            #     location=location_data,
            #     external_key="test"
            # )

if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())