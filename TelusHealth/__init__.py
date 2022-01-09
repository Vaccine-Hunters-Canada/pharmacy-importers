import asyncio
import csv
import json
import os
from typing import List
import aiohttp
import datetime

from bs4.element import Tag
from vhc import VHC
from mockvhc import MockVHC
from bs4 import BeautifulSoup
import sys
import re

from vaccine_types import VaccineType

import azure.functions as func

# Detect if subtype is in blacklist (e.g. COVID-19 test or flu shot)
# To detect appointment subtypes which are not COVID-19 vaccine
def detectblacklist(text):
    blacklist = (r'\bflu\b', r'\binfluenza\b', r'\bantigen\b', r'\bpcr\b',
                r'\btest\b', r'\bscreening\b', r'\bsymptomatic\b')
    for x in blacklist:
        if re.search(x, text, re.IGNORECASE):
            return True
    return False

# Detect text from appointment subtype to determine vaccine type, age groups, etc.
def detecttags(text: str) -> List[str]:
    tags = []
    if re.search(r'\bpfizer\b', text, re.IGNORECASE):
        tags.append("Pfizer")
    if re.search(r'\bmoderna\b', text, re.IGNORECASE):
        tags.append("Moderna")
    if re.search(r'\bastrazeneca\b', text, re.IGNORECASE) or re.search(r'\bastra zeneca\b', text, re.IGNORECASE):
        tags.append("AstraZeneca")
    if re.search(r'\b1st dose\b', text, re.IGNORECASE) or re.search(r'\bdose 1\b', text, re.IGNORECASE):
        tags.append("1st Dose")
    if re.search(r'\b2nd dose\b', text, re.IGNORECASE) or re.search(r'\bdose 2\b', text, re.IGNORECASE):
        tags.append("2nd Dose")
    if re.search(r'\b3rd dose\b', text, re.IGNORECASE) or re.search(r'\bdose 3\b', text, re.IGNORECASE) or re.search(r'\bbooster\b', text, re.IGNORECASE):
        tags.append("3rd Dose")
    if re.search(r'\b5-11\b', text, re.IGNORECASE) or re.search(r'\bpediatric\b', text, re.IGNORECASE) or re.search(r'\bpaediatric\b', text, re.IGNORECASE):
        tags.append("Ages 5-11")
    if re.search(r'\b12\+\b', text, re.IGNORECASE) or re.search(r'\b12 yrs\b', text, re.IGNORECASE) or re.search(r'\b12 and up\b', text, re.IGNORECASE):
        tags.append("Ages 12+")
    return tags

# Search tags to find first mentioned vaccine type, or return VaccineType.UNKNOWN if not found
def tags2vaccinetype(tags: List[str]) -> VaccineType:
    for tag in tags:
        if tag == "Pfizer":
            return VaccineType.PFIZER
        elif tag == "Moderna":
            return VaccineType.MODERNA
        elif tag == "AstraZeneca":
            return VaccineType.ASTRAZENECA
    return VaccineType.UNKNOWN

# Go to https://pharmaconnect.ca/Appointment/{"id"} and get list of subtypes
async def get_appointment_subtypes(id : str) -> dict:
    output = {} # Dictionary containing valid subtypes

    # Get appointment page
    url = f'https://pharmaconnect.ca/Appointment/{id}'

    async with aiohttp.ClientSession() as session:
        html = await session.get(url)
        if html.status == 200:
            page = BeautifulSoup(await html.text(), 'html.parser')
            dropdown = page.find("select",id="book-appointment-welcome-service-type-list")
            if type(dropdown) is not Tag: # No match
                return {}
            options = dropdown.findAll("option")
            types = list(map(lambda x: x.attrs["value"], options))
            if '' in types:
                types.remove('')

            # If this pharmacy lists ImmunizationCovid in first menu
            if "ImmunizationCovid" in types:
                # Look for submenu (2nd menu)
                dropdownsubtype = page.find("select",id="book-appointment-welcome-service-subtype-list")
                if type(dropdownsubtype) is not Tag: # No match
                    return {}
                optionssubtype = dropdownsubtype.findAll("option")
                # Get all dropdown options except blank string
                for subtype in optionssubtype:
                    dataservicetype = subtype.attrs["data-service-type"]
                    if dataservicetype == "ImmunizationCovid":
                        key = subtype.attrs["value"]
                        value = subtype.text
                        output[key] = value
        else:
            raise ConnectionError 
    return output

async def main(mytimer: func.TimerRequest | None, stateblob, dryrun = False) -> str:
    telus_csv = open('TelusHealth/telus-health-locations.csv')
    telus_locations = csv.DictReader(telus_csv)

    state = {}
    newstate = {}
    if stateblob:
        state = json.load(stateblob)

    async with aiohttp.ClientSession() as session:

        if dryrun == False:
            vhc = VHC(
                base_url=os.environ.get('BASE_URL'),
                api_key=os.environ.get('API_KEY'),
                org_id=os.environ.get('VHC_ORG_TELUS_HEALTH'),
                session=session
            )
        else:
            vhc = MockVHC()

        notifications = {
            'ON': [],
            'AB': []
        }
        for location in telus_locations:

            # Skip rows with missing postal code
            if not location.get('postal'):
                continue

            try:
                subtypes = await get_appointment_subtypes(location["id"])
            except ConnectionError:
                continue
            if subtypes == {}: # No subtypes
                continue

            available = False

            for subtype in subtypes:
                url = f'https://pharmaconnect.ca/Appointment/{location["id"]}/Slots?serviceType=ImmunizationCovid&serviceSubTypeId={subtype}&utcOffset=-300'
                html = await session.get(url)
                if html.status == 200:
                    page = BeautifulSoup(await html.text(), 'html.parser')
                    # Check for error like "The pharmacy currently has no availability for this type of service."
                    error = page.findAll(text="The pharmacy currently has no availability for this type of service.")
                    if len(error) == 1:
                        available = False
                    else:
                        # Check for div containing dates
                        dates = page.findAll('div', class_='b-days-selection appointment-availability__days-item')
                        available = bool(dates)
                else: # Response status is not 200
                    continue

                # Check if subtype is on blacklist (e.g. COVID-19 test or flu shot). If so, ignore
                if detectblacklist(subtypes[subtype]):
                    continue
                # Detect tags
                tags = detecttags(subtypes[subtype])
                vaccine_type = tags2vaccinetype(tags)

                location_data = {
                    'line1': location['address'].replace('<br>', ' ').strip(),
                    'province': location['province'].strip(),
                    'postcode': ''.join(location['postal'].split()),
                    'name': location['name'].strip(),
                    'phone': location['phone'].strip(),
                    'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}',
                    'tags': tags
                }

                await vhc.add_availability(
                    num_available=1 if available else 0,
                    num_total=1 if available else 0,
                    vaccine_type=vaccine_type.value,
                    location=location_data,
                    external_key=location['id']
                )

                if available:
                    name = f'{location_data["name"]} \n ({location_data["line1"]}) \n'
                    newstate[location["id"]] = name
                    if not state.get(location["id"]):
                        if location_data["province"].upper() in ["ON", "ONTARIO"]:
                            notifications['ON'].append({
                                'name': name,
                                'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}'
                            })
                        elif location_data["province"].upper() in ["AB", "ALBERTA"]:
                            notifications['AB'].append({
                                'name': name,
                                'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}'
                            })
            
            await vhc.notify_discord('Telus Health Pharmacies', notifications['ON'], os.environ.get('DISCORD_PHARMACY_ON'))
            await vhc.notify_discord('Telus Health Pharmacies', notifications['AB'], os.environ.get('DISCORD_PHARMACY_AB'))

            return json.dumps(newstate)