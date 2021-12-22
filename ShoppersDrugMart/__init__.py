import os
import json
import aiohttp
import logging
from vhc import VHC

VACCINES = {
    "Pfizer 1st Dose": {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 1)",
        "tags": ["12+ Year Olds", "Pfizer", "1st Dose"],
    },
    "Pfizer 2nd Dose": {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 2)",
        "tags": ["12+ Year Olds", "Pfizer", "2nd Dose"],
    },
    "Pfizer 3rd Dose": {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 3 or Booster Dose)",
        "tags": ["12+ Year Olds", "Pfizer", "3rd Dose"],
    },
    "Pfizer 5-11 1st Dose": {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Pediatric Dose 1)",
        "tags": ["5-11 Year Olds", "Pfizer", "1st Dose"],
    },
    "Pfizer 5-11 2nd Dose": {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Pediatric Dose 2)",
        "tags": ["5-11 Year Olds", "Pfizer", "2nd Dose"],
    },
    "Moderna 1st Dose": {
        "type": 3,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 1)",
        "tags": ["12+ Year Olds", "Moderna", "1st Dose"],
    },
    "Moderna 2nd Dose": {
        "type": 3,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 2)",
        "tags": ["12+ Year Olds", "Moderna", "2nd Dose"],
    },
    "Moderna 3rd Dose": {
        "type": 3,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 3 or Booster Dose)",
        "tags": ["12+ Year Olds", "Moderna", "3rd Dose"],
    },
}

ENTERPRISE= "SDM"
TENANT_ID = "edfbb1a3-aca2-4ee4-bbbb-9237237736c4"
URL = "https://gql.medscheck.medmeapp.com/graphql"
HEADERS = {
    "authority": "gql.medscheck.medmeapp.com",
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    "sec-ch-ua-mobile": "?0",
    "authorization": "",
    "content-type": "application/json",
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "x-tenantid": TENANT_ID,
    "sec-ch-ua-platform": '"macOS"',
    "origin": "https://shoppersdrugmart.medmeapp.com",
    "referer": "https://shoppersdrugmart.medmeapp.com/",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "accept-language": "en-US,en;q=0.9",
}

def slugify(s: str) -> str:
    return s.replace(" ", "_")

async def get_available_pharmacies(session, appointment_type_name):
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
      "enterpriseName": ENTERPRISE,
    }
    response = await session.post(URL, json={"query": query, "variables": variables})
    try:
        body = await response.json()
        return body["data"]["publicGetEnterprisePharmacies"]
    except (json.decoder.JSONDecodeError, KeyError, IndexError):
        logging.error(f"Failed to fetch data for appointment type '{appointment_type_name}'")
        return []


async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:

        vhc = VHC(
            base_url=os.environ.get("BASE_URL"),
            api_key=os.environ.get("API_KEY"),
            org_id=os.environ.get("VHC_ORG_SHOPPERS_DRUG_MART"),
            session=session,
        )

        for vaccine_name, vaccine_data in VACCINES.items():
            pharmacies = await get_available_pharmacies(session, vaccine_data["appointment_type_name"])
            for pharmacy in pharmacies:
                external_key = f"shoppersdrugmart-{pharmacy['storeNo']}-{slugify(vaccine_name)}"
                available = not pharmacy["appointmentTypes"][0]["isWaitlisted"]
                location = {
                    "line1": f"{pharmacy['pharmacyAddress']['streetNumber']} {pharmacy['pharmacyAddress']['streetName']}",
                    "city": pharmacy["pharmacyAddress"]["city"],
                    "province": pharmacy["pharmacyAddress"]["province"],
                    "postcode": pharmacy["pharmacyAddress"]["postalCode"].replace(" ", ""),
                    "name": pharmacy["name"],
                    "phone": pharmacy["pharmacyContact"]["phone"],
                    "url": f"https://shoppersdrugmart.medmeapp.com/{pharmacy['storeNo']}/schedule/{pharmacy['appointmentTypes'][0]['id']}",
                    "available": available,
                    "type": vaccine_data["type"],
                    "tags": vaccine_data["tags"]
                }

                await vhc.add_availability(
                    num_available=1 if available else 0,
                    num_total=1 if available else 0,
                    vaccine_type=vaccine_data["type"],
                    location=location,
                    external_key=external_key,
                )
