# Mock Vaccine Hunter class which does nothing but print to screen

from vaccine_types import VaccineType


class MockVHC:
    async def add_availability(self, num_available: int, num_total: int, vaccine_type: VaccineType, location: dict[str, str], external_key: str):
        print(f"Num available: {num_available}")
        print(f"Num total: {num_total}")
        print(f"Vaccine type: {vaccine_type}")
        print(f"Location: {location}")
        print(f"External key: {external_key}")

    async def notify_discord(self, title: str, availabilities, discord_url: str | None):
        print("Notifying Discord")
        print(f"Title: {title}")
        print(f"Availabilities: {availabilities}")
        print(f"Discord URL: {discord_url}")