import html
import json
import requests
import textwrap
import yaml


headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'gazelle-origin',
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
    def __init__(self, api_key):
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.headers.update({'Authorization': api_key})

    def request(self, action, **kwargs):
        ajaxpage = 'https://redacted.ch/ajax.php'
        params = {'action': action}
        params.update(kwargs)

        r = self.session.get(ajaxpage, params=params, allow_redirects=False, timeout=30)
        if r.status_code == 401 or r.status_code == 403:
            raise GazelleAPIError('unauthorized', 'Authentication error: ' + r.json()['error'])
        if r.status_code != 200:
            raise GazelleAPIError('request',
                'Could not retrieve origin data. Try again later. (status {0})'.format(r.status_code))

        parsed = json.loads(r.content)
        if parsed['status'] != 'success':
            raise GazelleAPIError('request-json', 'Could not retrieve origin data. Check the torrent ID/hash or try again later.')

        return parsed['response']

    def _make_table(self, dict):
        k_width = max(len(html.unescape(k)) for k in dict.keys()) + 2
        result = ''
        for k,v in dict.items():
            if v == "''":
                v = '~'
            result += "".join((html.unescape((k + ':').ljust(k_width)), v)) + '\n'
        return result

    def get_torrent_info(self, hash=None, id=None):
        info = self.request('torrent', hash=hash, id=id)
        group = info['group']
        torrent = info['torrent']

        if group['categoryName'] != 'Music':
            raise GazelleAPIError('music', 'Not a music torrent')
        
        # build artist name
        artists = group['musicInfo']['artists']
        if len(artists) == 1:
            artists = artists[0]['name']
        elif len(artists) == 2:
            artists = '{0} & {1}'.format(artists[0]['name'], artists[1]['name'])
        else:
            artists = 'Various Artists'

        # build full main artists name list
        mainArtist = group["musicInfo"]["artists"]
        if len(mainArtist) >= 1:
            mainArtistOutput = []    
            for artist in mainArtist:
                mainArtistOutput.append(artist['name']) 
            mainArtist = (', '.join(mainArtistOutput))    

        # build full featured artists name list
        featuredArtist = group["musicInfo"]["with"]
        if len(featuredArtist) >= 1:
            featuredArtistOutput = []    
            for artist in featuredArtist:
                featuredArtistOutput.append(artist['name']) 
            featuredArtist = (', '.join(featuredArtistOutput))   

        # build full producer artists name list
        producerArtist = group["musicInfo"]["producer"]
        if len(producerArtist) >= 1:
            producerArtistOutput = []    
            for artist in producerArtist:
                producerArtistOutput.append(artist['name']) 
            producerArtist = (', '.join(producerArtistOutput))    

        # build full dj artists name list
        djArtist = group["musicInfo"]["dj"]
        if len(djArtist) >= 1:
            djArtistOutput = []    
            for artist in djArtist:
                djArtistOutput.append(artist['name']) 
            djArtist = (', '.join(djArtistOutput))    

        # build full remix artists name list
        remixArtist = group["musicInfo"]["remixedBy"]
        if len(remixArtist) >= 1:
            remixArtistOutput = []    
            for artist in remixArtist:
                remixArtistOutput.append(artist['name']) 
            remixArtist = (', '.join(remixArtistOutput))     

        # build full composer artists name list
        composerArtist = group["musicInfo"]["composers"]
        if len(composerArtist) >= 1:
            composerArtistOutput = []    
            for artist in composerArtist:
                composerArtistOutput.append(artist['name']) 
            composerArtist = (', '.join(composerArtistOutput))      

        # build full conductor artists name list
        conductorArtist = group["musicInfo"]["conductor"]
        if len(conductorArtist) >= 1:
            conductorArtistOutput = []    
            for artist in conductorArtist:
                conductorArtistOutput.append(artist['name']) 
            conductorArtist = (', '.join(conductorArtistOutput))  

        ''' # This is code that works and will download the cover to whatever directory you run the script from
        # it is not tested or gauranteed to work 
        # downloads cover as RedCover
        redcover = requests.get(group['wikiImage']) 
        file = open("redCover.jpg", "wb")
        file.write(redcover.content)
        file.close()'''

        # Maps release type numbers to their sting values
        releaseNumber = group['releaseType']        
        if releaseNumber == 1:
            releaseTypes = "Album"
        elif releaseNumber == 3:
            releaseTypes = "Soundtrack"
        elif releaseNumber == 5:
            releaseTypes = "EP"
        elif releaseNumber == 6:
            releaseTypes = "Anthology"
        elif releaseNumber == 7:
            releaseTypes = "Compilation"
        elif releaseNumber == 9:
            releaseTypes = "Single"
        elif releaseNumber == 11:
            releaseTypes = "Live album"
        elif releaseNumber == 13:
            releaseTypes = "Remix"
        elif releaseNumber == 14:
            releaseTypes = "Bootleg"
        elif releaseNumber == 15:
            releaseTypes = "Interview"
        elif releaseNumber == 16:
            releaseTypes = "Mixtape"
        elif releaseNumber == 17:
            releaseTypes = "Demo"
        elif releaseNumber == 18:
            releaseTypes = "Concert Recording"
        elif releaseNumber == 19:
            releaseTypes = "DJ Mix"
        elif releaseNumber == 21:
            releaseTypes = "Unknown"  
        else:
            releaseTypes = "none"
        
        # If the api can return empty tags
        if not 'tags' in group:
            group['tags'] = ''
        if group['tags'] is None:
            group['tags'] = ''
        dict = {k:html.unescape(v) if isinstance(v, str) else v for k,v in {
            'Artist':                  artists,
            'Name':                    group['name'],
            'Release type':            releaseTypes,
            'Record label':            torrent['remasterRecordLabel'],
            'Catalog number':          torrent['remasterCatalogueNumber'],
            'Edition year':            torrent['remasterYear'] or '',
            'Edition':                 torrent['remasterTitle'],
            'Tags':                    str(', '.join(str(tag) for tag in group['tags'])),
            'Main artists':            mainArtist or '',
            'Featured artists':        featuredArtist or '', 
            'Producers':               producerArtist or '',
            'Remix artists':           remixArtist or '',
            'DJs':                     djArtist or '',    
            'Composers':               composerArtist or '',
            'Conductors':              conductorArtist or '',  
            'Original year':           group['year'] or '',
            'Original release label':  group['recordLabel'] or '',
            'Original catalog number': group['catalogueNumber'] or '',
            'Media':                   torrent['media'],
            'Log':                     '{0}%'.format(torrent['logScore']) if torrent['hasLog'] else '',
            'Format':                  torrent['format'],
            'Encoding':                torrent['encoding'],
            'Directory':               torrent['filePath'],
            'Size':                    torrent['size'],
            'File count':              torrent['fileCount'],
            'Info hash':               torrent['infoHash'],
            'Uploaded':                torrent['time'],
            'Permalink':               'https://redacted.ch/torrents.php?torrentid={0}'.format(torrent['id']),      
            'Cover':                   group['wikiImage']
        }.items()}

        dump = yaml.dump(dict, width=float('inf'), sort_keys=False, allow_unicode=True)

        out = {}
        for line in dump.strip().split('\n'):
            key, value = line.split(':', 1)
            if key == 'Uploaded' or key == 'Encoding':
                value = value.replace("'", '')
            out[key] = value.strip()

        result = self._make_table(out) + '\n'

        comment = html.unescape(torrent['description']).strip('\r\n')
        if comment:
            comment = textwrap.indent(comment, '  ', lambda line: True)
            result += 'Comment: |-\n{0}\n\n'.format(comment)

        out = []
        for el in html.unescape(torrent['fileList']).replace('}}}', '').split('|||'):
            name, size = el.split('{{{')
            out.append({'Name': name, 'Size': int(size)})
        result += yaml.dump({'Files': out}, width=float('inf'), allow_unicode=True)

        groupDescription = html.unescape(group['wikiBody']).strip('\r\n')
        if groupDescription:
            groupDescription = textwrap.indent(groupDescription, '  ', lambda line: True)
            result += '\n\nDescription: |-\n{0}\n\n'.format(groupDescription)

        return result
