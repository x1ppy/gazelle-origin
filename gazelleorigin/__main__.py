#!/usr/bin/env python3
import argparse
import io
import os
import re
import subprocess
import sys
import yaml
from hashlib import sha1
from . import GazelleAPI, GazelleAPIError, Orpheus


EXIT_CODES = {
    'hash': 3,
    'music': 4,
    'unauthorized': 5,
    'request': 6,
    'request-json': 7,
    'api-key': 8,
    'tracker': 9,
    'input-error': 10
}

_TRACKER_TOKENS = ("RED_API_KEY", "OPS_SESSION_COOKIE")
_VALID_TRACKERS = ("red", "flacsfor.me", "ops", "opsfet.ch")

_HANDLERS = {
        "red": {"class": GazelleAPI, "token_key": "RED_API_KEY"},
        "flacsfor.me": {"class": GazelleAPI, "token_key": "RED_API_KEY"},
        "ops": {"class": Orpheus, "token_key": "OPS_SESSION_COOKIE"},
        "opsfet.ch": {"class": Orpheus, "token_key": "OPS_SESSION_COOKIE"}
        }


parser = argparse.ArgumentParser(
    description='Fetches torrent origin information from Gazelle-based music trackers',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='Either ORIGIN_TRACKER or --tracker must be set to a supported tracker:\n'
           '  redacted.ch: "RED", or any string containing "flacsfor.me"\n'
           '  orpheus.network: "OPS"'
)
parser.add_argument('torrent', nargs='+', help='torrent identifier, which can be either its info hash, torrent ID, permalink, or path to torrent file(s) whose name or computed info hash should be used')
parser.add_argument('--out', '-o', help='Path to write origin data (default: print to stdout).', metavar='file')
parser.add_argument('--tracker', '-t', metavar='tracker',
    help='Tracker to use. Optional if the ORIGIN_TRACKER environment variable is set.')
parser.add_argument('--api-key', metavar='key',
    help='API key. Optional if the <TRACKER>_API_KEY (e.g., RED_API_KEY) environment variable is set.')
parser.add_argument('--env', '-e', nargs=1, metavar='file', help='file to load environment variables from')
parser.add_argument('--post', '-p', nargs='+', metavar='file', default=[], help='script(s) to run after each output is written.\n'
                    'These scripts have access to environment variables with info about the item including OUT, ARTIST, NAME, DIRECTORY, EDITION, YEAR, FORMAT, ENCODING')
parser.add_argument('--recursive', '-r', action='store_true', help='recursively search directories for files')
parser.add_argument('--no-hash', '-n', action='store_true', help='don\'t compute hash from torrent files')
parser.add_argument('--ignore-invalid', '-i', action='store_true', help='continue processing other arguments if an invalid id/hash is supplied')
parser.add_argument('--deduplicate', '-d', action='store_true', help='if specified, only one torrent with any given id/hash will be fetched')


api = None
args = None
fetched = {}
environment = {}


def main():
    global api, args, environment

    args = parser.parse_args()
    for script in args.post:
        if not os.path.isfile(script):
            print('Invalid post script: ' + script)
            sys.exit(EXIT_CODES['input-error'])
    environment = {'out': args.out if args.out else 'stdout'}

    if args.env:
        try:
            with open(args.env[0], 'r') as envfile:
                for line in envfile.readlines():
                    var = line.rstrip().split('=', 1)
                    if len(var) != 2:
                        if len(var) != 0:
                            print('Skipping invalid line in env file: ' + line)
                        continue
                    if var[0] in _TRACKER_TOKENS:
                        environment['api_key'] = var[1]
                    elif var[0] == 'ORIGIN_TRACKER':
                        environment['tracker'] = var[1]
                    else:
                        environment[var[0]] = var[1]
        except IOError:
            print('Unable to open file ' + args.env[0])
            sys.exit(EXIT_CODES['input-error'])

    if args.tracker:
        environment['tracker'] = args.tracker
    elif os.environ.get('ORIGIN_TRACKER'):
        environment['tracker'] = os.environ.get('ORIGIN_TRACKER')

    if not environment.get('tracker'):
        print('Tracker must be provided using either --tracker or setting the ORIGIN_TRACKER environment variable.',
                file=sys.stderr)
        sys.exit(EXIT_CODES['tracker'])

    if not any(tracker in environment['tracker'].lower() for tracker in _VALID_TRACKERS):
        print('Invalid tracker: {0}'.format(environment['tracker']), file=sys.stderr)
        sys.exit(EXIT_CODES['tracker'])
    
    environment['tracker'] = environment['tracker'].lower()

    if args.api_key:
        environment['api_key'] = args.api_key
    elif any(os.environ.get(tracker) for tracker in _TRACKER_TOKENS):
        for t_token in _TRACKER_TOKENS: # RED_API_KEY, OPS_SESSION_COOKIE
            token_key = _HANDLERS[environment['tracker']].get(t_token)
            if token_key:
                environment['api_key'] = token_key
                break

    if not environment.get('api_key'): # Avoid KeyError
        print(f'API key must be provided using either --api-key or setting the {", ".join(_TRACKER_TOKENS)} environment variables.', file=sys.stderr)
        sys.exit(EXIT_CODES['api-key'])

    
    handler_class = _HANDLERS[environment['tracker']]["class"]

    try:
        api = handler_class(environment['api_key'])
    except GazelleAPIError as e:
        print('Error initializing Gazelle API client')
        sys.exit(EXIT_CODES[e.code])

    for arg in args.torrent:
        handle_input_torrent(arg, True, args.recursive)


"""
Parse hash or id of torrent
torrent can be an id, hash, url, or path
"""
def parse_torrent_input(torrent, walk=True, recursive=False):
    # torrent is literal infohash
    if re.match(r'^[\da-fA-F]{40}$', torrent):
        return {'hash': torrent}
    # torrent is literal id
    if re.match(r'^\d+$', torrent):
        return {'id': torrent}
    # torrent is valid path
    if os.path.exists(torrent):
        if walk and os.path.isdir(torrent):
            for path in map(lambda x: os.path.join(torrent, x), os.listdir(torrent)):
                handle_input_torrent(path, recursive, recursive)
            return 'walked'
        # If file/dir name is info hash use that
        filename = os.path.split(torrent)[-1].split('.')[0]
        if re.match(r'^[\da-fA-F]{40}$', filename):
            return {'hash': filename}
        # If torrent file compute the info hash
        if not args.no_hash and os.path.isfile(torrent) and os.path.split(torrent)[-1].endswith('.torrent'):
            global encode, decode
            if 'encode' not in globals() or 'decode' not in globals():
                try:
                    from bencoder import encode, decode
                except:
                    print('Found torrent file ' + torrent + ' but unable to load bencoder module to compute hash')
                    print('Install bencoder (pip install bencoder) then try again or pass --no-hash to not compute the hash')
                    if args.ignore_invalid:
                        return None
                    else:
                        sys.exit(EXIT_CODES['input-error'])
            with open(torrent, 'rb') as torrent:
                try:
                    decoded = decode(torrent.read())
                    info_hash = sha1(encode(decoded[b'info'])).hexdigest()
                except:
                    return None
                return {'hash': info_hash}
    # torrent is a URL
    url_match = re.match(r'.*torrentid=(\d+).*', torrent)
    if not url_match or url_match.lastindex < 1:
        return None
    return {'id': url_match[1]}


"""
Get torrent's info from GazelleAPI
torrent can be an id, hash, url, or path
"""
def handle_input_torrent(torrent, walk=True, recursive=False):
    parsed = parse_torrent_input(torrent, walk, recursive)
    if parsed == 'walked':
        return
    if not parsed:
        print('Invalid torrent ID, hash, file, or URL: ' + torrent, file=sys.stderr)
        if args.ignore_invalid:
            return
        sys.exit(EXIT_CODES['hash'])

    if args.deduplicate:
        if 'id' in parsed:
            if parsed['id'] in fetched:
                return
            fetched[parsed['id']] = True
        if 'hash' in parsed:
            if parsed['hash'] in fetched:
                return
            fetched[parsed['hash']] = True

    # Actually get the info from the API
    try:
        info = api.get_torrent_info(**parsed)
    except GazelleAPIError as e:
        if not args.ignore_invalid:
            skip = False
        elif e.code == 'request':
            # If server returned 500 series error then stop because server might be having trouble
            skip = int(str(e).split('(status ')[-1][:-1]) >= 500
        else:
            skip = e.code == 'request-json' or e.code == 'music'
        if skip:
            print('Got %s retrieving %s, skipping' % (str(e), torrent))
            return
        else:
            print(e, file=sys.stderr)
            sys.exit(EXIT_CODES[e.code])

    if args.out:
        with io.open(args.out, 'a' if os.path.exists(args.out) else 'w', encoding='utf-8') as f:
            f.write(info)
    else:
        print(info, end='')

    if args.post:
        fetched_info = yaml.load(info, Loader=yaml.SafeLoader)
        for script in args.post:
            subprocess.run(script, shell=True, env={k.upper(): str(v) for k, v in {**environment, **fetched_info}.items()})

if __name__ == '__main__':
    main()
