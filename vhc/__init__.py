import logging
import aiohttp
import datetime

class VHC:
    BASE_URL = 'vax-availability-api-staging.azurewebsites.net'
    API_KEY = 'Bearer'
    VHC_ORG = 0
    VACCINES = {
        3: 'Moderna',
        4: 'Pfizer',
        5: 'AstraZeneca'
    }

    def __init__(self, base_url, api_key, org_id, session):
        self.BASE_URL = base_url
        self.API_KEY = f'Bearer {api_key}'
        self.VHC_ORG = org_id
        self.session = session
        logging.debug({
            'BASE_URL': self.BASE_URL,
            'VHC_ORG': self.VHC_ORG
        })

    def request_path(self, path):
        return f'https://{self.BASE_URL}/api/v1/{path}'

    async def add_availability(self, num_available, num_total, vaccine_type, location, external_key):
        vaccine_name = self.VACCINES.get(vaccine_type, 'Unknown')
        va = {
                'numberAvailable': num_available,
                'numberTotal': num_total,
                'vaccine': vaccine_type,
                'inputType': 1,
                'tags': '',
                'organization': self.VHC_ORG,
                'line1': location['line1'],
                'city': location['city'],
                'province': location['province'],
                'postcode': ''.join(location['postcode'].split()),
                'name': location['name'],
                'phone': location['phone'],
                'active': 1,
                'url': location['url'],
                'tagsL': '',
                'tagsA': vaccine_name,
                'externalKey': external_key,
                'date': f'{datetime.datetime.utcnow().date()}T00:00:00+00:00'
            }
        
        response = await self.session.post(
            url=self.request_path(f'vaccine-availability/locations/key/{external_key}'),
            json=va,
            headers={ 'Authorization': self.API_KEY }
        )

        if response.status != 200:
            logging.error(f'VHC API Error - {response.status}')
            logging.error(await response.text())
        else:
            if num_available > 0 :
                logging.info(f'Available   - {vaccine_name: <11} - {location["name"]}')
            else:
                logging.info(f'Unavailable - {vaccine_name: <11} - {location["name"]}')