# Mock Vaccine Hunter class which does nothing but print to screen

class MockVHC:
    async def add_availability(self, num_available, num_total, vaccine_type, location, external_key):
        print(f"Num available: {num_available}")
        print(f"Num total: {num_total}")
        print(f"Vaccine type: {vaccine_type}")
        print(f"Location: {location}")
        print(f"External key: {external_key}")

    async def notify_discord(self, title, availabilities, discord_url):
        print("Notifying Discord")
        print(f"Title: {title}")
        print(f"Availabilities: {availabilities}")
        print(f"Discord URL: {discord_url}")
