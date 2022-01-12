import asyncio
import argparse
import logging
import sys
import Metro
import PharmacyBooking
import Rexall
import SaveOnFoods
import ShoppersDrugMart
import Sobeys
import TelusHealth
import Walmart

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help="Mode to test")
    args = parser.parse_args()

    if args.mode == 'metro':
        asyncio.run(Metro.run_importer(dryrun=True))
    elif args.mode == 'pharmacybooking':
        asyncio.run(PharmacyBooking.run_importer(mytimer=None, dryrun=True))
    elif args.mode == 'rexall':
        asyncio.run(Rexall.run_importer(dryrun=True))
    elif args.mode == 'saveonfoods':
        asyncio.run(SaveOnFoods.run_importer(dryrun=True))
    elif args.mode == "shoppersdrugmart":
        asyncio.run(ShoppersDrugMart.run_importer(dryrun=True))
    elif args.mode == "sobeys":
        asyncio.run(Sobeys.run_importer(mytimer=None, stateblob=None, dryrun=True))
    elif args.mode == "telushealth":
        asyncio.run(TelusHealth.run_importer(mytimer=None, stateblob=None, dryrun=True))
    elif args.mode == "walmart":
        asyncio.run(Walmart.run_importer(mytimer=None, stateblob=None, dryrun=True))
    else:
        print("Invalid mode")