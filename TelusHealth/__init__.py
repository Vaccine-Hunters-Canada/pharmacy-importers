import asyncio
import os
import csv
import json
import aiohttp
import datetime
# from vhc import VHC
from bs4 import BeautifulSoup
import sys

# import azure.functions as func

async def main():
#async def main(mytimer: func.TimerRequest, stateblob) -> str:
    telus_csv = open('TelusHealth/telus-health-locations.csv')
    telus_locations = csv.DictReader(telus_csv)

    #state = {}
    #newstate = {}
    #if stateblob:
    #    state = json.load(stateblob)

    async with aiohttp.ClientSession() as session:

        # vhc = VHC(
        #     base_url=os.environ.get('BASE_URL'),
        #     api_key=os.environ.get('API_KEY'),
        #     org_id=os.environ.get('VHC_ORG_TELUS_HEALTH'),
        #     session=session
        # )

        # notifications = {
        #     'ON': [],
        #     'AB': []
        # }
        for location in telus_locations:

            if not location.get('postal'):
                continue

            available = 0

            url = f'https://pharmaconnect.ca/Appointment/{location["id"]}/Slots?serviceType=ImmunizationCovid'
            html = await session.get(url)
            if html.status == 200:
                page = BeautifulSoup(await html.text(), 'html.parser')
                # Check for error like "The pharmacy currently has no availability for this type of service."
                error = page.findAll(text="The pharmacy currently has no availability for this type of service.")
                if len(error) == 1:
                    available = 0
                else:
                    # Check for div containing dates
                    dates = page.findAll('div', class_='b-days-selection appointment-availability__days-item')
                    available = bool(dates)
                    error1 = page.findAll(text="This time slot is no longer available. Please select another time slot.")
                    error2 = page.findAll(text="Appointments for the selected date are fully booked. Please pick another day.")
                    error3 = page.findAll(text="The pharmacy is currently offline. This may be because their computer is turned off or the pharmacy is having internet connection issues. Please try again later or contact your pharmacy if this situation persists.")
                    if len(error1) > 0:
                        print("This time slot is no longer available. Please select another time slot.")
                    elif len(error2) > 0:
                        print("Appointments for the selected date are fully booked. Please pick another day.")
                    elif len(error3) > 0:
                        print("The pharmacy is currently offline. This may be because their computer is turned off or the pharmacy is having internet connection issues. Please try again later or contact your pharmacy if this situation persists.")
                    elif available == False:
                        print(page)
                        print("Unavailable but no error")
                    else:
                        print("Available")
            else:
                print(location["id"])
                print("404 error")
                continue

            location_data = {
                'line1': location['address'].replace('<br>', ' ').strip(),
                'province': location['province'].strip(),
                'postcode': ''.join(location['postal'].split()),
                'name': location['name'].strip(),
                'phone': location['phone'].strip(),
                'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}',
            }

            print(location_data)

            # await vhc.add_availability(
            #     num_available=1 if available else 0,
            #     num_total=1 if available else 0,
            #     vaccine_type=1,
            #     location=location_data,
            #     external_key=location['id']
            # )

        #     if available:
        #         name = f'{location_data["name"]} \n ({location_data["line1"]}) \n'
        #         newstate[location["id"]] = name
        #         if not state.get(location["id"]):
        #             if location_data["province"].upper() in ["ON", "ONTARIO"]:
        #                 notifications['ON'].append({
        #                     'name': name,
        #                     'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}'
        #                 })
        #             elif location_data["province"].upper() in ["AB", "ALBERTA"]:
        #                 notifications['AB'].append({
        #                     'name': name,
        #                     'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}'
        #                 })
        
        # await vhc.notify_discord('Telus Health Pharmacies', notifications['ON'], os.environ.get('DISCORD_PHARMACY_ON'))
        # await vhc.notify_discord('Telus Health Pharmacies', notifications['AB'], os.environ.get('DISCORD_PHARMACY_AB'))

        # return json.dumps(newstate)

if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main()) 