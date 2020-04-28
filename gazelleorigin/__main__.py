#!/usr/bin/env python3
import argparse
import io
import os
import re
import sys
from . import GazelleAPI, GazelleAPIError


EXIT_CODES = {
    'hash': 3,
    'music': 4,
    'unauthorized': 5,
    'request': 6,
    'request-json': 7,
    'api-key': 8,
    'tracker': 9,
}

parser = argparse.ArgumentParser(
    description='Fetches torrent origin information from Gazelle-based music trackers',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='Either ORIGIN_TRACKER or --tracker must be set to a supported tracker:\n'
           '  redacted.ch: "RED", or any string containing "flacsfor.me"'
)
parser.add_argument('id', help='Torrent identifier, which can be either its info hash,\n'
                               'torrent ID, or permalink.')
parser.add_argument('--out', '-o', help='Path to write origin data (default: print to stdout).', metavar='file')
parser.add_argument('--tracker', '-t', metavar='tracker',
    help='Tracker to use. Optional if the ORIGIN_TRACKER environment variable is set.')
parser.add_argument('--api-key', metavar='key',
    help='API key. Optional if the <TRACKER>_API_KEY (e.g., RED_API_KEY) environment variable is set.')


def main():
    args = parser.parse_args()

    api_key = args.api_key if args.api_key else os.environ.get('RED_API_KEY')
    if not api_key:
        print('API key must be provided using either --api-key or setting the <TRACKER>_API_KEY environment variable.', file=sys.stderr)
        sys.exit(EXIT_CODES['api-key'])

    tracker = args.tracker if args.tracker else os.environ.get('ORIGIN_TRACKER')
    if not tracker:
        print('Tracker must be provided using either --tracker or setting the ORIGIN_TRACKER environment variable.',
                file=sys.stderr)
        sys.exit(EXIT_CODES['tracker'])
    if tracker.lower() != 'red' and 'flacsfor.me' not in tracker.lower():
        print('Invalid tracker: {0}'.format(tracker), file=sys.stderr)
        sys.exit(EXIT_CODES['tracker'])

    try:
        api = GazelleAPI(api_key)

        if re.match(r'^[\da-fA-F]{40}$', args.id):
            info = api.get_torrent_info(hash=args.id)
        elif re.match(r'^\d+$', args.id):
            info = api.get_torrent_info(id=args.id)
        else:
            match = re.match(r'.*torrentid=(\d+)', args.id)
            if not match:
                print('Invalid torrent ID or hash', file=sys.stderr)
                sys.exit(EXIT_CODES['hash'])
            info = api.get_torrent_info(id=match[1])
    except GazelleAPIError as e:
        print(e, file=sys.stderr)
        sys.exit(EXIT_CODES[e.code])

    if args.out:
        with io.open(args.out, 'w', encoding='utf-8') as f:
            f.write(info)
    else:
        print(info, end="")


if __name__ == '__main__':
    main()
