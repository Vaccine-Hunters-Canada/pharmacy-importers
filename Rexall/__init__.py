import os
import json
import aiohttp
import logging
from vhc import VHC

class MedMeAppInterface:
    TENANT_ID = "edfbb1a3-aca2-4ee4-bbbb-9237237736c4"
    URL = "https://gql.medscheck.medmeapp.com/graphql"

    def __init__(self, enterprise_name, subdomain, org_id, vaccines):
        self.enterprise_name = enterprise_name
        self.subdomain = subdomain
        self.org_id = org_id
        self.vaccines = vaccines

    def headers(self):
        return {
            "authority": "gql.medscheck.medmeapp.com",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            "sec-ch-ua-mobile": "?0",
            "authorization": "",
            "content-type": "application/json",
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "x-tenantid": self.TENANT_ID,
            "sec-ch-ua-platform": '"macOS"',
            "origin": f"https://{self.subdomain}.medmeapp.com",
            "referer": f"https://{self.subdomain}.medmeapp.com/",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9",
        }

    async def get_available_pharmacies(self, session, appointment_type_name):
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
            }
            }
        }
        """
        variables = {
            "appointmentTypeName": appointment_type_name,
            "enterpriseName": self.enterprise_name,
        }
        response = await session.post(self.URL, json={"query": query, "variables": variables})
        try:
            body = await response.json()
            return body["data"]["publicGetEnterprisePharmacies"]
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            logging.error(
                f"Failed to fetch data for appointment type '{appointment_type_name}'"
            )
            return []

    async def update_availabilities(self):
        async with aiohttp.ClientSession(headers=self.headers()) as session:
            vhc = VHC(
                base_url=os.environ.get("BASE_URL"),
                api_key=os.environ.get("API_KEY"),
                org_id=self.org_id,
                session=session,
            )

            # Generate a lookup of external ID to pharmacy
            # As we see each pharmacy, add it to the lookup if it isn't yet there
            # Then, update its tags and availability
            pharmacies: dict[str, Pharmacy] = {}

            for vaccine_data in self.vaccines:
                for pharmacy_data in await self.get_available_pharmacies(session, vaccine_data["appointment_type_name"]):
                    pharmacy = Pharmacy(self.subdomain, pharmacy_data)

                    # If the pharmacy doesn't exist in the mapping yet, add it
                    # If it does exist, use the existing object instead
                    if pharmacy.external_key in pharmacies:
                        pharmacy = pharmacies[pharmacy.external_key]
                    else:
                        pharmacies[pharmacy.external_key] = pharmacy

                    # Update it with values from this data
                    pharmacy.available |= Pharmacy.is_available(pharmacy_data)
                    pharmacy.tags.update(vaccine_data["tags"])
                    pharmacy.vaccine_type = vaccine_data["type"]

            for external_key, pharmacy in pharmacies.items():
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

    @staticmethod
    def is_available(pharmacy):
        """Is the pharmacy currently accepting appointments?"""
        return not pharmacy["appointmentTypes"][0]["isWaitlisted"]

    def __init__(self, subdomain, pharmacy):
        self.subdomain = subdomain
        self.pharmacy = pharmacy
        self.vaccine_type = 3
        self.available = False
        self.tags = set()

    @property
    def external_key(self):
        return f"{self.subdomain}-{self.store_number}"

    @property
    def name(self):
        return self.pharmacy["name"]

    @property
    def address(self):
        return f"{self.pharmacy['pharmacyAddress']['streetNumber']} {self.pharmacy['pharmacyAddress']['streetName']}"

    @property
    def city(self):
        return self.pharmacy["pharmacyAddress"]["city"]

    @property
    def province(self):
        return self.pharmacy["pharmacyAddress"]["province"]

    @property
    def postal_code(self):
        return self.pharmacy["pharmacyAddress"]["postalCode"].replace(" ", "")

    @property
    def phone(self):
        return self.pharmacy["pharmacyContact"]["phone"]

    @property
    def website(self):
        return f"https://{self.subdomain}.medmeapp.com/{self.store_number}/schedule/"

    @property
    def store_number(self):
        return self.pharmacy['storeNo']

    @property
    def num_available(self):
        return 1 if self.available else 0

    @property
    def num_total(self):
        return 1 if self.available else 0

    def to_location(self):
        return {
            "line1": self.address,
            "city": self.city,
            "province": self.province,
            "postcode": self.postal_code,
            "name": self.name,
            "phone": self.phone,
            "url": self.website,
            "available": self.available,
            "type": self.vaccine_type,
            "tags": list(self.tags),
        }


async def main():
    await MedMeAppInterface(
        "REXALL",
        "rexall",
        os.environ.get("VHC_ORG_REXALL"),
        [
            {
                "type": 4,
                "appointment_type_name": "COVID-19 Vaccine (Dose 2 - Pfizer)",
                "tags": set(["12+ Year Olds", "Pfizer", "2nd Dose"]),
            },
            {
                "type": 4,
                "appointment_type_name": "COVID-19 Vaccine (Dose 3 - Pfizer)",
                "tags": set(["12+ Year Olds", "Pfizer", "3rd Dose"]),
            },
            {
                "type": 4,
                "appointment_type_name": "Pediatric (5-11) COVID-19 Vaccine (Dose 1)",
                "tags": set(["5-11 Year Olds", "Pfizer", "1st Dose"]),
            },
            {
                "type": 4,
                "appointment_type_name": "Pediatric (5-11) COVID-19 Vaccine (Dose 2)",
                "tags": set(["5-11 Year Olds", "Pfizer", "2nd Dose"]),
            },
            {
                "type": 3,
                "appointment_type_name": "COVID-19 Vaccine (Dose 2 - Moderna)",
                "tags": set(["12+ Year Olds", "Moderna", "2nd Dose"]),
            },
            {
                "type": 3,
                "appointment_type_name": "COVID-19 Vaccine (Dose 3 - Moderna)",
                "tags": set(["12+ Year Olds", "Moderna", "3rd Dose"]),
            },
            {
                "type": 5,
                "appointment_type_name": "COVID-19 Vaccine (Dose 2 - AstraZeneca/COVISHIELD)",
                "tags": set(["12+ Year Olds", "AstraZeneca", "2nd Dose"]),
            },
            {
                "type": 5,
                "appointment_type_name": "COVID-19 Vaccine (Dose 3 - AstraZeneca)",
                "tags": set(["12+ Year Olds", "AstraZeneca", "3rd Dose"]),
            },
        ]
    ).update_availabilities()