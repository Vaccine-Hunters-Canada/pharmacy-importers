import asyncio
import os
import csv
import json
import aiohttp
import datetime
# from vhc import VHC
from bs4 import BeautifulSoup
import sys
import re

# import azure.functions as func

appointmenttypes = ('ImmunizationCovid')

appointmentsubtypes = ('Immunization - COVID',
'Immunization - COVID Pfizer / Pfizer Booster (12+ years)',
'Immunization - COVID Pfizer (5-11 years)',
'Immunization - COVID Moderna (30+ years)',
'Immunization - COVID Moderna Booster (30+ years)',
'Kids Covid Vaccine (Age 5-11)',
'Immunization - COVID Vaccine',
'COVID-19 Screening Rapid Antigen Testing',
'Immunization - COVID Pfizer ',
'Immunization - COVID Moderna',
'Moderna 1st Dose',
'Moderna 2nd Dose',
'Astra Zeneca 2nd Dose',
'Pfizer Dose 1',
'Pfizer Dose 2',
'Pfizer Dose 3', 
'Pfizer Dose 4',
'Pfizer 5-11 Dose 1',
'Pfizer 5-11 Dose 2',
'Immunization - Paediatric COVID',
'Immunization -Moderna',
'Immunization - COVID Pfizer',
'Moderna Dose 1',
'Moderna Dose 2',
'Moderna Dose 3',
'MODERNA',
'Pfizer Pediatric Ages 5 to 11',
'Pfizer-Biontech COVID-19 Vaccine',
'Moderna COVID-19 Vaccine',
'MODERNA BOOSTER +30 YEARS OLD ',
'C-19 Vaccine 1st Dose (ADULT 12+)',
'C-19 Vaccine 2nd Dose (ADULT 12+)',
'C-19 Vaccine 3rd Dose (Adults 18+ & 3 months)',
'C-19 Pfizer 1st Dose (Children 5 - 11)',
'C-19 Pfizer 2nd Dose (Children 5 - 11)',
'COVID Vaccination - Age 30+ First Dose',
'COVID Vaccination - Age 30+ Second Dose',
'COVID Vaccination - Age 30+ Booster (Must be 22 weeks (154 days) after 2nd dose)',
'Covid 19 Vaccine 70+ ONLY',
'COVID Immunization - First Dose Aged 30+',
'COVID Immunization - 2nd Dose Aged 30+',
'COVID Immunization - 3rd Dose- Severely Immunocompromised - 28 days after 2nd Dose',
'COVID Booster - Aged 30-69 yrs (Must be 22 weeks or 154 days from 2nd Dose)',
'COVID Booster - Aged 70+ yrs -  (Must be 22 weeks or 154 days from 2nd Dose)',
'Pfizer',
'Moderna- 18 PLUS ',
'Immunization covid (Age 5-11 only ) ',
'Astra Zeneca Immunization - COVID',
'Immunization - COVID - Moderna',
'Covid 19 - Moderna-  THIRD DOSE ELIGIBLE PATIENTS ONLY',
'Immunization - COVID - Pfizer Dose (12+) 1st 2nd 3rd or Booster',
'COVID Kids Pfizer Dose (5-11) Single Child',
'Moderna 1st/2nd/3rd Doses',
'COVID Vaccine- Pfizer',
'COVID Vaccine- Astrazeneca',
'COVID Vaccine- Moderna',
'Immunization - Pfizer COVID (12 and up)',
'Immunization Pfizer COVID (5-11)',
'Pediatric Pfizer ',
'Moderna',
'COVID-19 Pfizer Immunization - First Dose (12+)',
'COVID-19 Moderna Immunization - First Dose (12+)',
'COVID-19 Moderna Immunization - Second Dose (12+)',
'COVID-19 Pfizer Immunization - Second Dose (12+)',
'COVID-19 Moderna Immunization - Third Dose (12+)',
'COVID-19 Pfizer Immunization - Third Dose (12+)',
'COVID-19 Pediatric Immunization - First Dose (5+)',
'COVID Pfizer Vaccine 12+',
'COVID-19 VACCINATION PFIZER',
'MODERNA VACCINE ',
'Immunization - COVID FOR 5-11 YRS',
'Pfizer COVID Vaccine (12 yrs and older)',
'Moderna Dose 1 or Dose 2 (18 years and older)',
'Immunization - COVID age 12+ Pfizer',
'Covid Pfizer age 5-11',
'Immunization - Pediatric covid',
'COVID-19 Vaccination')

# ['COVID-19 Screening', 'Care Plan Review', 'Immunization - COVID', 'Immunization - Flu Shot', 'Immunization - Other', 'Smoking Cessation Consultation', 'Travel Immunization Consultation', 'Medication Review', 'Immunization - COVID Pfizer / Pfizer Booster (12+ years)', 'Immunization - COVID Pfizer (5-11 years)', 'Immunization - COVID Moderna (30+ years)', 'Immunization - COVID Moderna Booster (30+ years)', 'Cannabis Consult', 'Shingrix #1', 'Shingrix #2', 'Prevnar13', 'Tetanus and Diphtheria-gov', 'Adacel -Tetanus/diphtheria/pertusis', 'Pneumovax23-gov', 'COVID-19 Test', 'Kids Covid Vaccine (Age 5-11)', 'Immunization - COVID Vaccine', 'COVID-19 Screening Rapid Antigen Testing', 'Immunization - 
# Influenza', 'Immunization - COVID Pfizer ', 'Immunization - COVID Moderna', 'Stocking Fitting', 'BOTOX for Dr. Lapp', 'Moderna 1st Dose', 'Moderna 2nd Dose', 'Astra Zeneca 2nd Dose', 'Pfizer Dose 1', 'Pfizer Dose 2', 'Pfizer Dose 3', 
# 'Pfizer Dose 4', 'Pfizer 5-11 Dose 1', 'Pfizer 5-11 Dose 2', 'Immunization - Paediatric COVID', 'COVID-19 Screening-Rapid Antigen Test', 'SYMPTOMATIC COVID PCR TEST ', 'Immunization -Moderna', 'Immunization - COVID Pfizer', 'Immunization -flu', 'Moderna Dose 1', 'Moderna Dose 2', 'Moderna Dose 3', 'MODERNA', 'Pfizer Pediatric Ages 5 to 11', 'Pfizer-Biontech COVID-19 Vaccine', 'Moderna COVID-19 Vaccine', 'MODERNA BOOSTER +30 YEARS OLD ', 'Immunization - Flu Shot (Regular)', 'Immunization - Flu Shot High Dose (over 65 years old)', 'PCR COVID-19 Test (Government, $0)', 'Rapid Antigen Test ($40+tax)', 'C-19 Vaccine 1st Dose (ADULT 12+)', 'C-19 Vaccine 2nd Dose (ADULT 12+)', 'C-19 Vaccine 3rd Dose 
# (Adults 18+ & 3 months)', 'C-19 Pfizer 1st Dose (Children 5 - 11)', 'C-19 Pfizer 2nd Dose (Children 5 - 11)', 'Covid-19 Antibody Test', 'COVID Vaccination - Age 30+ First Dose', 'COVID Vaccination - Age 30+ Second Dose', 'COVID Vaccination - Age 30+ Booster (Must be 22 weeks (154 days) after 2nd dose)', 'Wellness Clinic Day', 'Pharmacist At Home Consultation', 'Covid 19 Vaccine 70+ ONLY', 'Flu Shot Under 65', 'Flu Shot 65+', 'COVID Immunization - First Dose Aged 30+', 'COVID Immunization - 2nd Dose Aged 30+', 'COVID Immunization - 3rd Dose- Severely Immunocompromised - 28 days after 2nd Dose', 'COVID Booster - Aged 30-69 yrs (Must be 22 weeks or 154 days from 2nd Dose)', 'COVID Booster - Aged 
# 70+ yrs -  (Must be 22 weeks or 154 days from 2nd Dose)', 'Pfizer', 'Moderna- 18 PLUS ', 'Immunization covid (Age 5-11 only ) ', 'Astra Zeneca Immunization - COVID', 'Immunization - COVID - Moderna', 'Covid 19 - Moderna-  THIRD DOSE ELIGIBLE PATIENTS ONLY', 'Flu Shot - HIGH DOSE 65+ ONLY', 'Immunization - COVID - Pfizer Dose (12+) 1st 2nd 3rd or Booster', 'COVID Kids Pfizer Dose (5-11) Single Child', 'Immunization - Flu Shot All Ages (Starting November 1)', 'Immunization - Flu Shot 65+ (Senior Formulation)', 'Immunization - Standard-Dose Flu Shot (Ages 2+)', 'Immunization - High-Dose Flu Shot (Ages 65+)', 'Cannabis Consultation', 'Immunization - Flu Shot (Regular dose)', 'Moderna 1st/2nd/3rd Doses', 'COVID Vaccine- Pfizer', 'COVID Vaccine- Astrazeneca', 'COVID Vaccine- Moderna', 'Immunization - Pfizer COVID 
# (12 and up)', 'Immunization Pfizer COVID (5-11)', 'Pediatric Pfizer ', 'Moderna', 'Medication Review Follow-up', 'COVID-19 Pfizer Immunization - First Dose (12+)', 'COVID-19 Moderna Immunization - First Dose (12+)', 'COVID-19 Moderna 
# Immunization - Second Dose (12+)', 'COVID-19 Pfizer Immunization - Second Dose (12+)', 'COVID-19 Moderna Immunization - Third Dose (12+)', 'COVID-19 Pfizer Immunization - Third Dose (12+)', 'COVID-19 Pediatric Immunization - First Dose (5+)', 'Immunization - Flu Shot (High Dose)', 'Flu (Influenza) Vaccine', 'Asymptomatic COVID Rapid Test', 'COVID Pfizer Vaccine 12+', 'Flu Shot - LOW DOSE', 'COVID-19 Screening Symptomatic ', 'PCR Test (OHIP-drive thru)', 'PCR Test 
# (TakeHomeKit)', 'Rapid Antigen Test', 'COVID screening Symptomatic Drive thru', 'Sympatomatic Covid19 screening ', 'COVID-19 VACCINATION PFIZER', 'MODERNA VACCINE ', 'antigen rapid testing ', 'covid screening ', 'Immunization - COVID 
# FOR 5-11 YRS', 'Pfizer COVID Vaccine (12 yrs and older)', 'Moderna Dose 1 or Dose 2 (18 years and older)', 'Immunization - COVID age 12+ Pfizer', 'Covid Pfizer age 5-11', 'Immunization - Pediatric covid', 'General Consultation', 'Immunization - Shingles/Travel', 'Administer Medication via Injection', 'COVID-19 Vaccination']

# Detect if subtype is in blacklist (e.g. COVID-19 test or flu shot)
def detectblacklist(text):
    blacklist = (r'\bflu\b', r'\binfluenza\b', r'\bantigen\b', r'\bpcr\b',
                r'\btest\b', r'\bscreening\b', r'\bsymptomatic\b')
    for x in blacklist:
        if re.search(x, text, re.IGNORECASE):
            return True
    return False

# Detect text from vaccine type
def detectvaccine(text):
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
            options = dropdown.findAll("option")
            types = list(map(lambda x: x.attrs["value"], options))
            if '' in types:
                types.remove('')

            # If this pharmacy lists ImmunizationCovid in first menu
            if "ImmunizationCovid" in types:
                # Look for submenu (2nd menu)
                dropdownsubtype = page.find("select",id="book-appointment-welcome-service-subtype-list")
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

async def main():
#async def main(mytimer: func.TimerRequest, stateblob) -> str:
    telus_csv = open('TelusHealth/telus-health-locations.csv')
    telus_locations = csv.DictReader(telus_csv)

    #state = {}
    #newstate = {}
    #if stateblob:
    #    state = json.load(stateblob)

    async with aiohttp.ClientSession() as session:

        # vhc = VHC(
        #     base_url=os.environ.get('BASE_URL'),
        #     api_key=os.environ.get('API_KEY'),
        #     org_id=os.environ.get('VHC_ORG_TELUS_HEALTH'),
        #     session=session
        # )

        # notifications = {
        #     'ON': [],
        #     'AB': []
        # }
        for location in telus_locations:

            # Skip rows with missing postal code
            if not location.get('postal'):
                continue

            # # Get appointment page
            # url = f'https://pharmaconnect.ca/Appointment/{location["id"]}'

            # html = await session.get(url)
            # if html.status == 200:
            #     page = BeautifulSoup(await html.text(), 'html.parser')
            #     #print(page)
            #     dropdown = page.find("select",id="book-appointment-welcome-service-type-list")
            #     options = dropdown.findAll("option")
            #     #print(dropdown)
            #     # Get all dropdown options except blank string
            #     types = list(map(lambda x: x.attrs["value"], options))
            #     if '' in types:
            #         types.remove('')
            #     print(types)
            #     for x in types:
            #         if x not in alltypes:
            #             alltypes.append(x)

            #     if "ImmunizationCovid" in types:
            #         # Look for submenu
            #         dropdownsubtype = page.find("select",id="book-appointment-welcome-service-subtype-list")
            #         # Determine if submenu is visible
            #         #if "d-none" not in dropdownsubtype.attrs["class"]:
            #         optionssubtype = dropdownsubtype.findAll("option")
            #         print(dropdownsubtype)
            #         # Get all dropdown options except blank string
            #         #subtypes = list(map(lambda x: x.attrs["data-service-type"], optionssubtype))
            #         subtypes = list(map(lambda x: x.text, optionssubtype))
            #         if '' in types:
            #             subtypes.remove('')
            #         print(subtypes)
            #         for x in subtypes:
            #             if x not in allsubtypes:
            #                 allsubtypes.append(x)

            try:
                types = await get_appointment_subtypes(location["id"])
            except ConnectionError:
                continue
            if types != {}:
                print(types)

            available = False

            for subtype in types:
                print(subtype)
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
                        error1 = page.findAll(text="This time slot is no longer available. Please select another time slot.")
                        error2 = page.findAll(text="Appointments for the selected date are fully booked. Please pick another day.")
                        error3 = page.findAll(text="The pharmacy is currently offline. This may be because their computer is turned off or the pharmacy is having internet connection issues. Please try again later or contact your pharmacy if this situation persists.")
                        if len(error1) > 0:
                            print("This time slot is no longer available. Please select another time slot.")
                        elif len(error2) > 0:
                            print("Appointments for the selected date are fully booked. Please pick another day.")
                        elif len(error3) > 0:
                            print("The pharmacy is currently offline. This may be because their computer is turned off or the pharmacy is having internet connection issues. Please try again later or contact your pharmacy if this situation persists.")
                        elif available == False:
                            print(page)
                            print("Unavailable but no error")
                        else:
                            print("Available")
                else:
                    print(location["id"])
                    print("404 error")
                    continue

                location_data = {
                    'line1': location['address'].replace('<br>', ' ').strip(),
                    'province': location['province'].strip(),
                    'postcode': ''.join(location['postal'].split()),
                    'name': location['name'].strip(),
                    'phone': location['phone'].strip(),
                    'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}',
                }

                print(location_data)
                print(available)
                if detectblacklist(types[subtype]):
                    print("Blacklist")
                print(types[subtype])
                print(detectvaccine(types[subtype]))
                print("Done")

                # await vhc.add_availability(
                #     num_available=1 if available else 0,
                #     num_total=1 if available else 0,
                #     vaccine_type=1,
                #     location=location_data,
                #     external_key=location['id']
                # )

            #     if available:
            #         name = f'{location_data["name"]} \n ({location_data["line1"]}) \n'
            #         newstate[location["id"]] = name
            #         if not state.get(location["id"]):
            #             if location_data["province"].upper() in ["ON", "ONTARIO"]:
            #                 notifications['ON'].append({
            #                     'name': name,
            #                     'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}'
            #                 })
            #             elif location_data["province"].upper() in ["AB", "ALBERTA"]:
            #                 notifications['AB'].append({
            #                     'name': name,
            #                     'url': f'https://pharmaconnect.ca/Appointment/{location["id"]}'
            #                 })
            
            # await vhc.notify_discord('Telus Health Pharmacies', notifications['ON'], os.environ.get('DISCORD_PHARMACY_ON'))
            # await vhc.notify_discord('Telus Health Pharmacies', notifications['AB'], os.environ.get('DISCORD_PHARMACY_AB'))

            # return json.dumps(newstate)

if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main()) 