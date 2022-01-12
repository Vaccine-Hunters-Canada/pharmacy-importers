from medmeapp import MedMeAppInterface
from vaccine_types import VaccineType

TENANT_ID = "edfbb1a3-aca2-4ee4-bbbb-9237237736c4"
ENTERPRISE_NAME = "SDM"
SUBDOMAIN = "shoppersdrugmart"
VACCINES = [
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 1)",
        "tags": set(["12+ Year Olds", "Pfizer", "1st Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 2)",
        "tags": set(["12+ Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Dose 3 or Booster Dose)",
        "tags": set(["12+ Year Olds", "Pfizer", "3rd Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Pediatric Dose 1)",
        "tags": set(["5-11 Year Olds", "Pfizer", "1st Dose"]),
    },
    {
        "type": VaccineType.PFIZER,
        "appointment_type_name": "COVID-19 Vaccine (Pfizer Pediatric Dose 2)",
        "tags": set(["5-11 Year Olds", "Pfizer", "2nd Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 1)",
        "tags": set(["12+ Year Olds", "Moderna", "1st Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 2)",
        "tags": set(["12+ Year Olds", "Moderna", "2nd Dose"]),
    },
    {
        "type": VaccineType.MODERNA,
        "appointment_type_name": "COVID-19 Vaccine (Moderna Dose 3 or Booster Dose)",
        "tags": set(["12+ Year Olds", "Moderna", "3rd Dose"]),
    },
]

async def main() -> None:
    await run_importer()

async def run_importer(dryrun: bool = False) -> None:
    await MedMeAppInterface(TENANT_ID, ENTERPRISE_NAME, SUBDOMAIN, VACCINES, dryrun).update_availabilities()