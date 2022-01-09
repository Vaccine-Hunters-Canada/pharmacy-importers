import asyncio
import argparse
import sys
import TelusHealth

if __name__ == '__main__':
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help="Mode to test")
    args = parser.parse_args()

    if args.mode == 'telushealth':
        asyncio.run(TelusHealth.main(mytimer=None, stateblob=None, dryrun=True))
    else:
        print("Invalid mode")