# import os
import json
from urllib import request
import aiohttp
import asyncio
import logging
from urllib.request import Request, urlopen
# from vhc import VHC


class CostcoLocation:
    def __init__(self, name, address, city, province, postal, phone, teleHippoId, booking_url):
        self.name = "Costco " + name
        self.address = address
        self.city = city
        self.province = province
        self.postal = postal
        self.phone = phone
        self.teleHippoId = teleHippoId
        self.booking_url = booking_url

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


async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        costco_location_url = "https://www.costcopharmacy.ca/assets/json/app.clinics.json"
        costco_location_request = Request(costco_location_url, headers={'User-Agent': 'Mozilla/5.0'})
        costco_location_response = urlopen(costco_location_request).read().decode()
        costco_location_json = json.loads(costco_location_response)

        pharmacies = []

        for location in costco_location_json:
            booking_url = "https://b.telehippo.com/o/{}".format(location["teleHippoId"])
            costco_location = CostcoLocation(location["name"], location["address"], location["city"], location["provinceCode"], location["postalCode"], location["phone"], location["teleHippoId"], booking_url)
            pharmacies.append(costco_location)

        test_id = "w533"

        site_url = "https://apipharmacy.telehippo.com/api/c/{}/graphql".format(test_id)
        query = """
            \"query {
                cRetailerWithSetting (data:{slug:\\\"w533\\\"}) { 
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
            }\"
        """
        
        print(query)
        response = await session.post(site_url, json={"query": query})
        try:
            body = await response.json()
            print(body)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            logging.error(
                "Failed to fetch data"
            )
            return []


loop = asyncio.get_event_loop()
loop.run_until_complete(main())