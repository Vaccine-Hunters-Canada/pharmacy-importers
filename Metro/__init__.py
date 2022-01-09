from medmeapp import MedMeAppInterface
from vaccine_types import VaccineType


TENANT_ID = "c906edeb-2f2a-4867-b167-f882555e44bb"
ENTERPRISE_NAME = "METRO"
SUBDOMAIN = "metro"
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
        "appointment_type_name": "COVID-19 Vaccine (Dose 1 - Pediatric)",
        "tags": set(["5-11 Year Olds", "Pfizer", "1st Dose"]),
    },
]

async def main(dryrun: bool = False) -> None:
    await MedMeAppInterface(TENANT_ID, ENTERPRISE_NAME, SUBDOMAIN, VACCINES, dryrun).update_availabilities()