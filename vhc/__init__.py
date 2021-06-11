import logging
import aiohttp
from datetime import datetime

class VHC:
    BASE_URL = 'vax-availability-api-staging.azurewebsites.net'
    API_KEY = 'Bearer'
    VHC_ORG = 0

    def __init__(self, base_url, api_key, org_id, session):
        self.BASE_URL = base_url
        self.API_KEY = f'Bearer {api_key}'
        self.VHC_ORG = org_id
        self.session = session

    def request_path(self, path):
        return f'https://{self.BASE_URL}/api/v1/{path}'

    async def get_location(self, uuid):
        url = self.request_path(f'locations/external/{uuid}')
        response = await self.session.get(url, headers={'accept': 'application/json'})
        data = None
        try:
            data = await response.json()
        except aiohttp.client_exceptions.ContentTypeError: # if location does not exist
            if not data:
                return None
        return data['id']

    async def create_location(self, url, external_key, name, address, postal_code, province):
        data = {
            'name': name,
            'postcode': postal_code,
            'external_key': external_key,
            'line1': address,
            'active': 1,
            'url': url,
            'organization': self.VHC_ORG,
            'province': province
        }

        headers = {'Authorization': self.API_KEY, 'Content-Type': 'application/json'}
        location_post = await self.session.post(self.request_path('locations/expanded'), headers=headers, json=data)
        location_id = await location_post.text()
        return location_id
    
    async def get_availability(self, location):
        params = {
            'locationID': location,
            'min_date': str(datetime.now().date())
        }
        url = self.request_path(f'vaccine-availability/location/')
        response = await self.session.get(url, params=params)
        if response.status != 200:
            logging.error(f'Got Response: {response.status}')
            return None
        availabilities = await response.json()
        if len(availabilities) > 0:
            return availabilities[0]['id']
        return None

    async def create_availability(self, location, available):
        date = str(datetime.now().date())+'T00:00:00Z'
        vacc_avail_body = {
            "numberAvailable": available,
            "numberTotal": available,
            "vaccine": 1,
            "inputType": 1,
            "tags": "",
            "location": location,
            "date": date
        }
        
        vacc_avail_headers = {'accept': 'application/json', 'Authorization': self.API_KEY, 'Content-Type':'application/json'}
        response = await self.session.post(self.request_path('vaccine-availability'), headers=vacc_avail_headers, json=vacc_avail_body)
        data = await response.json()
        return data['id']

    async def update_availability(self, id, location, available):
        date = str(datetime.now().date())+'T00:00:00Z'
        vacc_avail_body = {
            "numberAvailable": available,
            "numberTotal": available,
            "vaccine": 1,
            "inputType": 1,
            "tags": "",
            "location": location,
            "date": date
        }
        
        vacc_avail_headers = {'accept': 'application/json', 'Authorization': self.API_KEY, 'Content-Type':'application/json'}
        response = await self.session.put(self.request_path(f'vaccine-availability/{id}'), headers=vacc_avail_headers, json=vacc_avail_body)
        data = await response.json()
        return data['id']

    async def get_or_create_location(self, url, external_key, name, address, postal_code, province):
        location = await self.get_location(external_key)
        if location is None:
            logging.info(f'Create Location [{external_key}]: {name}')
            location = await self.create_location(url, external_key, name, address, postal_code, province)
        else:
            logging.info(f'Found Location  [{external_key}]: {name}')
        return location

    async def create_or_update_availability(self, location, available):
        availability = await self.get_availability(location)
        if availability is None:
            availability = await self.create_availability(location, available)
            logging.info(f'Created Availability: {available} [{availability}]')
        else:
            availability = await self.update_availability(availability, location, available)
            logging.info(f'Updated Availability: {available} [{availability}]')
        return availability