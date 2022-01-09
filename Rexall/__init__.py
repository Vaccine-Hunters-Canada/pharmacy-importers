from medmeapp import MedMeAppInterface
from vaccine_types import VaccineType


TENANT_ID = "f10d8ca0-ec52-4a28-aabd-9bd3388dab34"
ENTERPRISE_NAME = "REXALL"
SUBDOMAIN = "rexall"
VACCINES = [
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Dose 2 - Pfizer)",
        "tags": set(["12+ Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Dose 3 - Pfizer)",
        "tags": set(["12+ Year Olds", "Pfizer", "3rd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "Pediatric (5-11) COVID-19 Vaccine (Dose 1)",
        "tags": set(["5-11 Year Olds", "Pfizer", "1st Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "Pediatric (5-11) COVID-19 Vaccine (Dose 2)",
        "tags": set(["5-11 Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Dose 2 - Moderna)",
        "tags": set(["12+ Year Olds", "Moderna", "2nd Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Dose 3 - Moderna)",
        "tags": set(["12+ Year Olds", "Moderna", "3rd Dose"]),
    },
    {
        "type": VaccineType.ASTRAZENECA,
        "appointment_type_name": "COVID-19 Vaccine (Dose 2 - AstraZeneca/COVISHIELD)",
        "tags": set(["12+ Year Olds", "AstraZeneca", "2nd Dose"]),
    },
    {
        "type": VaccineType.ASTRAZENECA,
        "appointment_type_name": "COVID-19 Vaccine (Dose 3 - AstraZeneca)",
        "tags": set(["12+ Year Olds", "AstraZeneca", "3rd Dose"]),
    },
]

async def main(dryrun: bool = False) -> None:
    await MedMeAppInterface(TENANT_ID, ENTERPRISE_NAME, SUBDOMAIN, VACCINES, dryrun).update_availabilities()