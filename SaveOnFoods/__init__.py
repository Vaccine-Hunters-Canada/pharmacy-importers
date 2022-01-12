from medmeapp import MedMeAppInterface
from vaccine_types import VaccineType

TENANT_ID = "c79c2656-0a6d-4e20-98bf-15a775eaae53"
ENTERPRISE_NAME = "SOF"
SUBDOMAIN = "saveonfoodspharmacy"
VACCINES = [
    {
        "type": VaccineType.UNKNOWN,
        "appointment_type_name": "COVID-19 Vaccine (Dose 1)",
        "tags": set(["12+ Year Olds", "1st Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Dose 2 - Moderna)",
        "tags": set(["12+ Year Olds", "Moderna", "2nd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Dose 2 - Pfizer)",
        "tags": set(["12+ Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Dose 3 - Moderna)",
        "tags": set(["12+ Year Olds", "Moderna", "3rd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Dose 3 - Pfizer)",
        "tags": set(["12+ Year Olds", "Pfizer", "3rd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Dose 1) Children 5-11 yrs",
        "tags": set(["5-11 Year Olds", "Pfizer", "1st Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Dose 2) Children 5-11 yrs",
        "tags": set(["5-11 Year Olds", "Pfizer", "2nd Dose"]),
    },
]

async def main() -> None:
    await run_importer()

async def run_importer(dryrun: bool = False) -> None:
    await MedMeAppInterface(TENANT_ID, ENTERPRISE_NAME, SUBDOMAIN, VACCINES, dryrun).update_availabilities()