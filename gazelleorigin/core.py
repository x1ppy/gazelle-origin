import html
from pprint import pprint
import json
import requests
import textwrap
import yaml


headers = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "User-Agent": "gazelle-origin",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
}


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
        self.base = "https://redacted.ch"
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.headers.update({"Authorization": api_key})

    def request(self, action, **kwargs):
        params = {"action": action}
        params.update(kwargs)
        return self._get_parsed_response(params)

    def _get_parsed_response(self, params, cookies=None):
        ajaxpage = f"{self.base}/ajax.php"
        r = self.session.get(
            ajaxpage, params=params, allow_redirects=False, timeout=30, cookies=cookies
        )
        if r.status_code == 401 or r.status_code == 403:
            raise GazelleAPIError(
                "unauthorized", "Authentication error: " + r.json()["error"]
            )
        if r.status_code != 200:
            raise GazelleAPIError(
                "request",
                "Could not retrieve origin data. Try again later. (status {0})".format(
                    r.status_code
                ),
            )

        parsed = json.loads(r.content)
        if parsed["status"] != "success":
            raise GazelleAPIError(
                "request-json",
                "Could not retrieve origin data. Check the torrent ID/hash or try again later.",
            )

        return parsed["response"]

    @staticmethod
    def _make_table(dict):
        k_width = max(len(html.unescape(k)) for k in dict.keys()) + 2
        result = ""
        for k, v in dict.items():
            if v == "''":
                v = "~"
            result += "".join((html.unescape((k + ":").ljust(k_width)), v)) + "\n"
        return result

    def get_torrent_info(self, hash=None, id=None):
        info = self.request("torrent", hash=hash, id=id)
        group = info["group"]
        torrent = info["torrent"]

        if group["categoryName"] != "Music":
            raise GazelleAPIError("music", "Not a music torrent")

        artists = group["musicInfo"]["artists"]
        if len(artists) == 1:
            artists = artists[0]["name"]
        elif len(artists) == 2:
            artists = "{0} & {1}".format(artists[0]["name"], artists[1]["name"])
        else:
            artists = "Various Artists"

        dict = {
            k: html.unescape(v) if isinstance(v, str) else v
            for k, v in {
                "Artist": artists,
                "Name": group["name"],
                "Edition": torrent["remasterTitle"],
                "Edition year": torrent["remasterYear"] or "",
                "Media": torrent["media"],
                "Catalog number": torrent["remasterCatalogueNumber"],
                "Record label": torrent["remasterRecordLabel"],
                "Original year": group["year"] or "",
                "Format": torrent["format"],
                "Encoding": torrent["encoding"],
                "Log": "{0}%".format(torrent["logScore"]) if torrent["hasLog"] else "",
                "Directory": torrent["filePath"],
                "Size": torrent["size"],
                "File count": torrent["fileCount"],
                "Info hash": torrent.get("infoHash", "Unknown"),  # OPS fallback
                "Uploaded": torrent["time"],
                "Permalink": f"{self.base}/torrents.php?torrentid={torrent['id']}",
            }.items()
        }

        dump = yaml.dump(dict, width=float("inf"), sort_keys=False, allow_unicode=True)

        out = {}
        for line in dump.strip().split("\n"):
            key, value = line.split(":", 1)
            if key == "Uploaded" or key == "Encoding":
                value = value.replace("'", "")
            out[key] = value.strip()

        result = self._make_table(out) + "\n"

        comment = html.unescape(torrent["description"]).strip("\r\n")
        if comment:
            comment = textwrap.indent(comment, "  ", lambda line: True)
            result += "Comment: |-\n{0}\n\n".format(comment)

        out = []
        for el in html.unescape(torrent["fileList"]).replace("}}}", "").split("|||"):
            name, size = el.split("{{{")
            out.append({"Name": name, "Size": int(size)})
        result += yaml.dump({"Files": out}, width=float("inf"), allow_unicode=True)

        return result


class Orpheus(GazelleAPI):
    def __init__(self, session_cookie: str):
        self.base = "https://orpheus.network"
        self.session = requests.Session()
        self.cookies = {"session": session_cookie}
        self.session.headers.update(headers)

    def request(self, action, **kwargs):
        params = {"action": action}
        params.update(kwargs)
        return self._get_parsed_response(params, cookies=self.cookies)
