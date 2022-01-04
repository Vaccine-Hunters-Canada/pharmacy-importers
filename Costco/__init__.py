# import os
import json
from urllib import request
import aiohttp
import asyncio
import logging
from urllib.request import Request, urlopen
from datetime import datetime, timedelta
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


async def getSlots(retailer_id, start_date, covid_service_id):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        next_day = start_date + timedelta(days=1)
        formattedStartDate = start_date.strftime("%y-%m-%d")
        formattedNextDay = next_day.strftime("%y-%m-%d")
        slots_url = "https://apipharmacy.telehippo.com/api/c/{}/graphql".format(retailer_id)
        query = ("""
            query { 
                searchBookableWorkTimes (data:{retailerId:%s,startDate:\"20%s 04:00:00\",endDate:\"20%s 03:59:59\",serviceId:%s}) { 
                    workTimes { 
                        id,
                        startTimes,
                        endTimes,
                        startDate,
                        endDate 
                    }, 
                    events { 
                        id,
                        startTime,
                        endTime 
                    },
                    bookableDays,
                    nextAvailableDate,
                    isAvailable 
                }
            }
        """ % (retailer_id, formattedStartDate, formattedNextDay, covid_service_id))

        response = await session.post(slots_url, json={"query": query})
        try:
            body = await response.json()

            return body['data']['searchBookableWorkTimes']
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            logging.error(
                "Failed to fetch data"
            )
            return False

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

        # for pharmacy in pharmacies:
            # retailer_id = pharmacy.retailer_id
        retailer_id = 135

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
                    # print(service)

        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            logging.error(
                "Failed to fetch data"
            )
            return []
        
        for service in pharmacy.covid_services:
            # Start by calling it for today. This will give us information, including the bookable days, which we can then pass through to this function again.
            today_bookable_times = await getSlots(retailer_id, datetime.now(), service['id'])
            bookable_days = today_bookable_times['bookableDays']
            
            vaccine_duration = service['duration']
            
            if (len(bookable_days) != 0 and today_bookable_times['isAvailable'] == True):
                for bookable_day in bookable_days:
                    bookable_day_datetime = datetime.strptime(bookable_day, "%Y-%m-%d")
                    # Make sure bookable date is not in the past.
                    if datetime.now() > bookable_day_datetime:
                        continue

                    bookable_day_times = await getSlots(retailer_id, bookable_day_datetime, service['id'])
                    
                    # print(bookable_day_times)

                    # There are multiple start and end times in a given day sometimes
                    start_times = bookable_day_times['workTimes'][0]['startTimes'].split(",")
                    end_times = bookable_day_times['workTimes'][0]['endTimes'].split(",")

                    num_available = 0
                    current_event = bookable_day_times['events'].pop(0)

                    for i in range(len(start_times)):
                        current_start_time = start_times[i]
                        current_end_times = end_times[i]
                        current_start_datetime = datetime.strptime(bookable_day + " " + current_start_time, "%Y-%m-%d %H:%M:%S")
                        current_end_datetime = datetime.strptime(bookable_day + " " + current_end_times, "%Y-%m-%d %H:%M:%S")

                        # I know this is a bit of a gross way to get the right format, but it works...
                        formatted_current_end_time = (current_event['endTime'].split("+"))[0]
                        current_event_end_datetime = datetime.strptime(formatted_current_end_time, "%a %b %d %Y %H:%M:%S %Z")
                    
                        # Make sure the current appointment is after the start time we are looking at
                        while (current_event and current_start_datetime > current_event_end_datetime):
                            current_event = bookable_day_times['events'].pop(0)
                            formatted_current_end_time = (current_event['endTime'].split("+"))[0]
                            current_event_end_datetime = datetime.strptime(formatted_current_end_time, "%a %b %d %Y %H:%M:%S %Z")
                        
                        formatted_current_start_time = (current_event['startTime'].split("+"))[0]
                        current_event_start_datetime = datetime.strptime(formatted_current_start_time, "%a %b %d %Y %H:%M:%S %Z")

                        past_event = None
                        past_event_start_datetime = None
                        past_event_end_datetime = None

                        while (current_event_end_datetime < current_end_datetime):
                            # Not sure why, but occassionally two duplicates come through, so need to trap this and move on
                            if past_event_start_datetime == current_event_start_datetime:
                                current_event = bookable_day_times['events'].pop(0)

                                formatted_current_start_time = (current_event['startTime'].split("+"))[0]
                                current_event_start_datetime = datetime.strptime(formatted_current_start_time, "%a %b %d %Y %H:%M:%S %Z")
                                formatted_current_end_time = (current_event['endTime'].split("+"))[0]
                                current_event_end_datetime = datetime.strptime(formatted_current_end_time, "%a %b %d %Y %H:%M:%S %Z")
                                
                                continue
                            if past_event == None:
                                # If this is the first booked appointment, and there is no past events, that means there is an appointment before it
                                if current_event_start_datetime != current_start_datetime:
                                    num_available += 1
                                    
                            else:
                                if (past_event_end_datetime != current_event_start_datetime):
                                    # print(past_event_end_datetime)
                                    # print(past_event)
                                    # print(current_event_start_datetime)
                                    # print(current_event)
                                    num_available += 1

                            past_event = current_event
                            past_event_start_datetime = current_event_start_datetime
                            past_event_end_datetime = current_event_end_datetime

                            current_event = bookable_day_times['events'].pop(0)

                            formatted_current_start_time = (current_event['startTime'].split("+"))[0]
                            current_event_start_datetime = datetime.strptime(formatted_current_start_time, "%a %b %d %Y %H:%M:%S %Z")
                            formatted_current_end_time = (current_event['endTime'].split("+"))[0]
                            current_event_end_datetime = datetime.strptime(formatted_current_end_time, "%a %b %d %Y %H:%M:%S %Z")
                            
                    print(num_available)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())