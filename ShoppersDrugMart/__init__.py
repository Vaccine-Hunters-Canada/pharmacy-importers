import os
from medmeapp import MedMeAppInterface

TENANT_ID = "edfbb1a3-aca2-4ee4-bbbb-9237237736c4"
ENTERPRISE_NAME = "SDM"
SUBDOMAIN = "shoppersdrugmart"
ORG_ID = os.environ.get("VHC_ORG_SHOPPERS_DRUG_MART")
VACCINES = [
    {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 1)",
        "tags": set(["12+ Year Olds", "Pfizer", "1st Dose"]),
    },
    {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 2)",
        "tags": set(["12+ Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 3 or Booster Dose)",
        "tags": set(["12+ Year Olds", "Pfizer", "3rd Dose"]),
    },
    {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Pediatric Dose 1)",
        "tags": set(["5-11 Year Olds", "Pfizer", "1st Dose"]),
    },
    {
        "type": 4,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Pediatric Dose 2)",
        "tags": set(["5-11 Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": 3,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 1)",
        "tags": set(["12+ Year Olds", "Moderna", "1st Dose"]),
    },
    {
        "type": 3,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 2)",
        "tags": set(["12+ Year Olds", "Moderna", "2nd Dose"]),
    },
    {
        "type": 3,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 3 or Booster Dose)",
        "tags": set(["12+ Year Olds", "Moderna", "3rd Dose"]),
    },
]

async def main():
    await MedMeAppInterface(TENANT_ID, ENTERPRISE_NAME, SUBDOMAIN, ORG_ID, VACCINES).update_availabilities()