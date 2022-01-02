import os
from medmeapp import MedMeAppInterface


TENANT_ID = "f10d8ca0-ec52-4a28-aabd-9bd3388dab34"
ENTERPRISE_NAME = "REXALL"
SUBDOMAIN = "rexall"
ORG_ID = os.environ.get("VHC_ORG_REXALL")
VACCINES = [
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

async def main():
    await MedMeAppInterface(TENANT_ID, ENTERPRISE_NAME, SUBDOMAIN, ORG_ID, VACCINES).update_availabilities()