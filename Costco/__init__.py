# import os
import json
from urllib import request
import aiohttp
import asyncio
import logging
from urllib.request import Request, urlopen
# from vhc import VHC


class CostcoLocation:
    def __init__(self, name, address, city, province, postal, phone, telehippo_id, booking_url):
        self.name = "Costco " + name
        self.address = address
        self.city = city
        self.province = province
        self.postal = postal
        self.phone = phone
        self.telehippo_id = telehippo_id
        self.booking_url = booking_url
        self.retailer_id = -1
        self.covid_services = []
    
    @staticmethod
    def get_external_key(location):
        if location.retailer_id != -1:
            return f"costco-{location.retailer_id}"
        else:
            return ""

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.39 Safari/537.36",
    "Content-Type": "application/json",
    "cache-control": "no-cache",
    "Origin": "https://b.telehippo.com",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "referrer": "https://b.telehippo.com/",
    "referrerPolicy": "origin-when-cross-origin"
}


def getSlots(retailer_id, covid_service_id):
    return True

async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Get all Costco locations
        costco_location_url = "https://www.costcopharmacy.ca/assets/json/app.clinics.json"
        costco_location_request = Request(costco_location_url, headers={'User-Agent': 'Mozilla/5.0'})
        costco_location_response = urlopen(costco_location_request).read().decode()
        costco_location_json = json.loads(costco_location_response)

        pharmacies = []

        for location in costco_location_json:
            booking_url = "https://b.telehippo.com/o/{}".format(location["teleHippoId"])
            costco_location = CostcoLocation(location["name"], location["address"], location["city"], location["provinceCode"], location["postalCode"], location["phone"], location["teleHippoId"], booking_url)
            pharmacies.append(costco_location)

        for pharmacy in pharmacies:
            pharmacy_id = pharmacy.telehippo_id
            site_url = "https://apipharmacy.telehippo.com/api/c/{}/graphql".format(pharmacy_id)

            query = ("""
                query {
                    cRetailerWithSetting (data:{slug:\"%s\"}) { 
                        success,
                        error,
                        data { 
                            retailer { 
                                id,
                                name,
                                slug,
                                startTime,
                                endTime 
                            } 
                        }
                    }
                }
            """ % pharmacy_id)

            response = await session.post(site_url, json={"query": query})
            try:
                body = await response.json()
                pharmacy.retailer_id = body['data']['cRetailerWithSetting']['data']['retailer']['id']
            except (json.decoder.JSONDecodeError, KeyError, IndexError):
                logging.error(
                    "Failed to fetch data"
                )
                return []

        for pharmacy in pharmacies:
            retailer_id = pharmacy.retailer_id
            # retailer_id = 135

            appointments_url = "https://apipharmacy.telehippo.com/api/c/{}/graphql".format(retailer_id)
            query = ("""
                query { 
                    onlineBookableAppointmentTypes (data:{retailerId:%s}) { 
                        success,
                        error,
                        data {  
                            services { 
                                id,
                                name,
                                duration,
                                bookingMode,
                                description,
                                intakeFormType,
                                mainPageMode 
                            } 
                        } 
                    }
                }
            """ % retailer_id)
            
            response = await session.post(appointments_url, json={"query": query})
            try:
                body = await response.json()
                available_services = body['data']['onlineBookableAppointmentTypes']['data']['services']

                for service in available_services:
                    # This isn't super clear from the API, but I was able to derive the following:
                    # bookingMode = 0 - Shows up on the site
                    # bookingMode = 6 - Hidden from user-facing site
                    # mainPageMode = 0 - Accepting Bookable Appointments
                    # mainPageMode = 2 - Accepting Waitlist Signups
                    if (service['bookingMode'] == 0 and service['mainPageMode'] == 0 and "covid" in service['name'].lower()):
                        pharmacy.covid_services.append(service)

            except (json.decoder.JSONDecodeError, KeyError, IndexError):
                logging.error(
                    "Failed to fetch data"
                )
                return []


loop = asyncio.get_event_loop()
loop.run_until_complete(main())