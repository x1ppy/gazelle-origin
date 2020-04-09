import html
import io
import json
import os
import re
import requests
import textwrap
import yaml


headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'red-origin',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'}


class GazelleAPIError(Exception):
    def __init__(self, code, message):
        super().__init__()
        self.code = code
        self.message = message

    def __str__(self):
        return self.message


# GazelleAPI code is based off of REDbetter (https://github.com/Mechazawa/REDBetter-crawler).
class GazelleAPI:
    def __init__(self, session_cookie=None):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session_cookie = session_cookie.replace('session=', '')
        self.authkey = None
        self._login()

    def _login(self):
        mainpage = 'https://redacted.ch/'
        cookiedict = {"session": self.session_cookie}
        cookies = requests.utils.cookiejar_from_dict(cookiedict)

        self.session.cookies.update(cookies)

        try:
            res = self.session.get(mainpage, allow_redirects=False)
            if 'Set-Cookie' in res.headers and 'session=deleted' in res.headers['Set-Cookie']:
                raise ValueError('invalid')
        except Exception as e:
            if isinstance(e, ValueError) and str(e) == 'invalid':
                raise GazelleAPIError('login', 'Invalid or expired session cookie.')
            else:
                raise GazelleAPIError('login', 'Could not log in to RED. Check your session cookie or try again later.')

        accountinfo = self.request('index')
        self.authkey = accountinfo['authkey']

    def request(self, action, **kwargs):
        ajaxpage = 'https://redacted.ch/ajax.php'
        params = {'action': action}
        if self.authkey:
            params['auth'] = self.authkey
        params.update(kwargs)

        r = self.session.get(ajaxpage, params=params, allow_redirects=False)
        if r.status_code != 200:
            raise GazelleAPIError('request', 'Could not retrieve origin data. Try again later.')

        parsed = json.loads(r.content)
        if parsed['status'] != 'success':
            raise GazelleAPIError('request-json', 'Could not retrieve origin data. Check the torrent ID/hash or try again later.')

        return parsed['response']

    def get_torrent_info(self, hash=None, id=None):
        info = self.request('torrent', hash=hash, id=id)
        group = info['group']
        torrent = info['torrent']

        if group['categoryName'] != 'Music':
            raise GazelleAPIError('music', 'Not a music torrent')

        artists = group['musicInfo']['artists']
        if len(artists) == 1:
            artists = artists[0]['name']
        elif len(artists) == 2:
            artists = '{0} & {1}'.format(artists[0]['name'], artists[1]['name'])
        else:
            artists = 'Various Artists'

        dump = yaml.dump({
            'Artist':         artists,
            'Name':           group['name'],
            'Edition':        torrent['remasterTitle'],
            'Edition year':   torrent['remasterYear'] or '',
            'Media':          torrent['media'],
            'Catalog number': torrent['remasterCatalogueNumber'],
            'Record label':   torrent['remasterRecordLabel'],
            'Original year':  group['year'] or '',
            'Format':         torrent['format'],
            'Encoding':       torrent['encoding'],
            'Log':            '{0}%'.format(torrent['logScore']) if torrent['hasLog'] else '',
            'Directory':      torrent['filePath'],
            'Size':           torrent['size'],
            'File count':     torrent['fileCount'],
            'Info hash':      torrent['infoHash'],
            'Uploaded':       torrent['time'],
            'Permalink':      'https://redacted.ch/torrents.php?torrentid={0}'.format(torrent['id']),
        }, width=float('inf'), sort_keys=False, allow_unicode=True)

        out = {}
        for line in dump.strip().split('\n'):
            key, value = line.split(':', 1)
            if key == 'Uploaded' or key == 'Encoding':
                value = value.replace("'", '')
            out[key] = html.unescape(value.strip())

        result = make_table(out) + '\n'

        comment = html.unescape(torrent['description']).strip('\r\n')
        if comment:
            comment = textwrap.indent(comment, '  ')
            result += 'Comment: |-\n{0}\n\n'.format(comment)

        out = []
        for el in html.unescape(torrent['fileList']).replace('}}}', '').split('|||'):
            name, size = el.split('{{{')
            out.append({'Name': name, 'Size': int(size)})
        result += yaml.dump({'Files': out}, width=float('inf'), allow_unicode=True)

        return result

def make_table(dict):
    k_width = max(len(html.unescape(k)) for k in dict.keys()) + 2
    result = ''
    for k,v in dict.items():
        if v == "''":
            v = '~'
        result += "".join((html.unescape((k + ':').ljust(k_width)), v)) + '\n'
    return result
