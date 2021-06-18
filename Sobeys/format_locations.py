import csv
import sys
from pprint import pprint

if __name__ == "__main__":
    output = open('sobeys.csv', 'w')
    writer = csv.DictWriter(
        output,
        fieldnames=['id', 'name', 'postal', 'province', 'city', 'address']
    )

    writer.writeheader()

    print(f'Reading file: {sys.argv[1]}')
    with open(sys.argv[1]) as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(f'{row["Name"]}')
            address = row['sked__Address__c']
            address_parts = address.split(',')
            postal_code = address_parts.pop().strip().replace(' ', '')
            province = address_parts.pop().strip()
            city = address_parts.pop().strip()
            street_address = ' '.join(address_parts).strip()
            writer.writerow({
                'id': row['Id'],
                'name': row['Name'].replace('AstraZeneca', '').strip(),
                'postal': postal_code,
                'province': province,
                'city': city,
                'address': street_address
            })