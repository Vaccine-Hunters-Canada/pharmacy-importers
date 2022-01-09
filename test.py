import asyncio
import argparse
import sys
import Calendly

if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help="Mode to test")
    args = parser.parse_args()

    if args.mode == 'calendly':
        asyncio.run(Calendly.main(mytimer=None, stateblob=None, dryrun=True))
    else:
        print("Invalid mode")