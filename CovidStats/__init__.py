import os
import logging
import requests
import json
from datetime import datetime, timedelta

import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    yesterday_date_string = '{:%B %d, %Y}'.format(datetime.now() - timedelta(1))

    is_weekend = False

    if (datetime.now() - timedelta(1)).weekday() >= 5:
        is_weekend = True

    vaccination_url = f'https://api.opencovid.ca/timeseries?stat=avaccine&loc=prov&after={yesterday_date}&before={yesterday_date}'
    response = requests.get(vaccination_url)
    vaccination_response_body = json.loads(response.content)

    active_case_url = f'https://api.opencovid.ca/timeseries?stat=active&loc=prov&date={yesterday_date}'
    response = requests.get(active_case_url)
    active_cases_body = json.loads(response.content)

    cases_url = f'https://api.opencovid.ca/timeseries?stat=cases&loc=prov&date={yesterday_date}'
    response = requests.get(cases_url)
    cases_body = json.loads(response.content)

    discord_url = os.environ.get('DISCORD_STATS_WEBHOOK')

    vaccination_fields = []
    cases_fields = []
    totals_fields = []

    total_vaccinations = 0
    change_in_vaccinations = 0
    total_cases = 0
    change_in_total_cases = 0
    total_active_cases = 0
    change_in_total_active_cases = 0

    counter = 0

    if(is_weekend):
        vaccination_fields.append(
            {
                "name": "This data is from the weekend, so Alberta, BC, Quebec, NL, PEI, NT, and Nunavut did not report statistics.",
                "value" : "----------------------"
            }
        )

        cases_fields.append(
            {
                "name": "It is the weekend, so Alberta, BC, Quebec, NL, PEI, NT, and Nunavut do not report statistics",
                "value" : "----------------------"
            }
        )

        totals_fields.append(
            {
                "name": "It is the weekend, so Alberta, BC, Quebec, NL, PEI, NT, and Nunavut do not report statistics",
                "value" : "----------------------"
            }
        )
    for province in cases_body["cases"]:
        
        active_cases = active_cases_body["active"][counter]
        change_in_active_cases = ""
        
        if(active_cases["active_cases_change"] >= 0):
            change_in_active_cases = "+" + str(active_cases["active_cases_change"])
        else:
            change_in_active_cases = str(active_cases["active_cases_change"])

        cases_fields.append(
            {
                "value" : "Total Cases: " + str(province["cumulative_cases"]) + " (+" + str(province["cases"]) + "), Active Cases: " + str(active_cases["active_cases"]) + " (" + change_in_active_cases + ")",
                "name" : province["province"] 
            }
        )
        total_cases += province["cumulative_cases"]
        change_in_total_cases += province["cases"]
        total_active_cases += active_cases["active_cases"]
        change_in_total_active_cases += active_cases["active_cases_change"]

        counter += 1

    for province in vaccination_response_body["avaccine"]:
        
        vaccination_fields.append(
            {
                "value" : "Total Vaccinated: " + str(province["cumulative_avaccine"]) + " (+" + str(province['avaccine']) + " new vaccinations)",
                "name" : province["province"] 
            }
        )
        total_vaccinations += province["cumulative_avaccine"]
        change_in_vaccinations += province['avaccine']

    change_in_case_string = ""
    if(change_in_total_active_cases >= 0):
        change_in_case_string = "+" + str(change_in_total_active_cases)
    else:
        change_in_case_string = str(change_in_total_active_cases)

    totals_fields.append(
            {
                "value" : "Total Cases: " + str(total_cases) + " (+" + str(change_in_total_cases) + "), Active Cases: " + str(total_active_cases) + " (" + change_in_case_string + ")",
                "name" : "Canada-Wide Cases"
            }
        )

    totals_fields.append(
            {
                "value" : "Total Vaccinated: " + str(total_vaccinations) + " (+" + str(change_in_vaccinations) + " new vaccinations)",
                "name" : "Canada-Wide Vaccinations"
            }
        )

    data = {
        "username": "COVID Stat Bot",
        "embeds" : [
            {
                "title" : "Yesterdays (" + yesterday_date_string + ") Vaccination Stats",
                "fields" : vaccination_fields
            },
            {
                "title" : "Yesterdays (" + yesterday_date_string + ") Case Stats",
                "fields" : cases_fields
            },
            {
                "title" : "Yesterdays (" + yesterday_date_string + ") Combined Totals",
                "fields" : totals_fields
            }
        ]
    }

    result = requests.post(discord_url, json = data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(err)
    else:
        logging.info(f"Payload delivered successfully, code {result.status_code}.")
