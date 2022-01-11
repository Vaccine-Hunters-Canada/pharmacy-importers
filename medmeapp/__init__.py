import os
import json
from typing import List
import aiohttp
import logging

from aiohttp.client import ClientSession
from mockvhc import MockVHC
from vaccine_types import VaccineType
from vhc import VHC
import datetime

class MedMeAppInterface:
    URL = "https://gql.medscheck.medmeapp.com/graphql"

    def __init__(self, tenant_id: str, enterprise_name: str, subdomain: str, vaccines, dryrun: bool = False) -> None:
        self.tenant_id = tenant_id
        self.enterprise_name = enterprise_name
        self.subdomain = subdomain
        self.vaccines = vaccines
        self.dryrun = dryrun # Set to True for testing, False for production

    def headers(self) -> dict:
        return {
            "authority": "gql.medscheck.medmeapp.com",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            "sec-ch-ua-mobile": "?0",
            "authorization": "",
            "content-type": "application/json",
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "x-tenantid": self.tenant_id,
            "sec-ch-ua-platform": '"macOS"',
            "origin": f"https://{self.subdomain}.medmeapp.com",
            "referer": f"https://{self.subdomain}.medmeapp.com/",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9",
        }

    async def get_available_pharmacies(self, session: ClientSession, appointment_type_name: str) -> List:
        query = """
        query publicGetEnterprisePharmacies($appointmentTypeName: String, $enterpriseName: String!, $storeNo: String) {
            publicGetEnterprisePharmacies(appointmentTypeName: $appointmentTypeName, enterpriseName: $enterpriseName, storeNo: $storeNo) {
            id
            name
            storeNo
            pharmacyAddress {
                unit
                streetNumber
                streetName
                city
                province
                country
                postalCode
                longitude
                latitude
            }
            pharmacyContact {
                phone
                email
            }
            appointmentTypes {
                id
                isWaitlisted
                bookingStartDate
                bookingEndDate
                waitlistCount
            }
        }
        }
        """
        variables = {
            "appointmentTypeName": appointment_type_name,
            "enterpriseName": self.enterprise_name,
        }
        response = await session.post(self.URL, json={"query": query, "variables": variables})
        if response.status == 200:
            try:
                body = await response.json()
                return body["data"]["publicGetEnterprisePharmacies"]
            except (json.decoder.JSONDecodeError, KeyError, IndexError, TypeError):
                logging.error(
                    f"Failed to fetch data for appointment type '{appointment_type_name}'"
                )
                return []
        else:
            return []
    
    async def get_available_timeslots(self, session: ClientSession, pharmacyId: str, appointmentTypeId: int) -> List:
        start_date = datetime.datetime.utcnow()
        end_date = start_date + datetime.timedelta(days=60) # Use approximately 2 months

        start_date_formatted = start_date.strftime('%Y-%m-%d')
        end_date_formatted = end_date.strftime('%Y-%m-%d')
        
        query = """
        query publicGetAvailableTimes($pharmacyId: String, $appointmentTypeId: Int!, $noOfPeople: Int!, $filter: AvailabilityFilter!) {
        publicGetAvailableTimes(pharmacyId: $pharmacyId, appointmentTypeId: $appointmentTypeId, noOfPeople: $noOfPeople, filter: $filter) {
            startDateTime
            endDateTime
            resourceId
            __typename
        }
        }
        """
        variables = {
            "appointmentTypeId": appointmentTypeId,
            "noOfPeople": 1,
            "pharmacyId": pharmacyId,
            "filter": {
                "endDate": end_date_formatted,
                "startDate": start_date_formatted
            }
        }
        response = await session.post(self.URL, json={"query": query, "variables": variables})
        if response.status == 200:
            body = await response.json()
            try:
                body = await response.json()
                return body["data"]["publicGetAvailableTimes"]
            except (json.decoder.JSONDecodeError, KeyError, IndexError, TypeError):
                logging.error(
                    f"Failed to fetch timeslots'"
                )
                return []
        else:
            return []          

    async def update_availabilities(self):
        async with aiohttp.ClientSession(headers=self.headers()) as session:
            if self.dryrun == False:
                vhc = VHC(
                   base_url=os.environ.get("BASE_URL"),
                   api_key=os.environ.get("API_KEY"),
                   org_id=os.environ.get("ORG_ID_MEDMEAPP"),
                   session=session,
                )
            else:
                vhc = MockVHC()

            # Generate a lookup of external ID to pharmacy
            # As we see each pharmacy, add it to the lookup if it isn't yet there
            # Then, update its tags and availability
            pharmacies: dict[str, Pharmacy] = {}

            for vaccine_data in self.vaccines:
                logging.info(f"Getting available pharmacies for {vaccine_data['appointment_type_name']}")
                for pharmacy_data in await self.get_available_pharmacies(session, vaccine_data["appointment_type_name"]):
                    id = pharmacy_data["id"]
                    appointmentTypeId = pharmacy_data["appointmentTypes"][0]["id"]

                    waitlisted = pharmacy_data["appointmentTypes"][0]["isWaitlisted"]
                    timeslots = None
                    if not waitlisted:
                        logging.info(f"Getting timeslots for pharmacy {id}")
                        timeslots = await self.get_available_timeslots(session, id, appointmentTypeId)
                        logging.info(f"{len(timeslots)} found")
                    else:
                        logging.info(f"Pharmacy {id} is waitlisted")

                    pharmacy = Pharmacy(self.subdomain, pharmacy_data)

                    # If the pharmacy doesn't exist in the mapping yet, add it
                    # If it does exist, use the existing object instead
                    if pharmacy.external_key in pharmacies:
                        pharmacy = pharmacies[pharmacy.external_key]
                    else:
                        pharmacies[pharmacy.external_key] = pharmacy

                    if timeslots is not None and len(timeslots) > 0:
                        pharmacy.available = True
                        pharmacy.num_available = len(timeslots)
                        pharmacy.num_total = len(timeslots)
                        pharmacy.tags.update(vaccine_data["tags"])
                        pharmacy.vaccine_type = vaccine_data["type"]

            for external_key, pharmacy in pharmacies.items():
                logging.info("Adding availability")
                await vhc.add_availability(
                    num_available=pharmacy.num_available,
                    num_total=pharmacy.num_total,
                    vaccine_type=pharmacy.vaccine_type,
                    location=pharmacy.to_location(),
                    external_key=external_key,
                )

class Pharmacy:
    """
    Represents a single instance of a pharmacy
    Provides methods for accessing data within the GraphQL response that was received
    """

    def __init__(self, subdomain: str, pharmacy: dict) -> None:
        self.subdomain = subdomain
        self.pharmacy = pharmacy
        self.vaccine_type = VaccineType.UNKNOWN # Unknown by default
        self.available = False
        self.num_available = 0
        self.num_total = 0
        self.tags = set()

    @property
    def external_key(self) -> str:
        return f"{self.subdomain}-{self.store_number}"

    @property
    def name(self) -> str:
        return self.pharmacy["name"]

    @property
    def address(self) -> str:
        return f"{self.pharmacy['pharmacyAddress']['streetNumber']} {self.pharmacy['pharmacyAddress']['streetName']}"

    @property
    def city(self) -> str:
        return self.pharmacy["pharmacyAddress"]["city"]

    @property
    def province(self) -> str:
        return self.pharmacy["pharmacyAddress"]["province"]

    @property
    def postal_code(self) -> str:
        return self.pharmacy["pharmacyAddress"]["postalCode"].replace(" ", "")

    @property
    def phone(self) -> str:
        return self.pharmacy["pharmacyContact"]["phone"]

    @property
    def website(self) -> str:
        return f"https://{self.subdomain}.medmeapp.com/{self.store_number}/schedule/"

    @property
    def store_number(self) -> str:
        return self.pharmacy['storeNo']

    def to_location(self) -> dict:
        return {
            "line1": self.address,
            "city": self.city,
            "province": self.province,
            "postcode": self.postal_code,
            "name": self.name,
            "phone": self.phone,
            "url": self.website,
            "available": self.available,
            "type": self.vaccine_type.value,
            "tags": list(self.tags),
        }
