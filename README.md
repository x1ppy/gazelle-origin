gazelle-origin
==============

`gazelle-origin` is a script that fetches and saves YAML torrent origin information from Gazelle-based music trackers.

Example output from `gazelle-origin`:

~~~
Artist:         Pink Floyd
Name:           The Dark Side of the Moon
Edition:        'Japan MFSL UltraDisc #1, 24 Karat Gold'
Edition year:   1988
Media:          CD
Catalog number: UDCD 517
Record label:   Mobile Fidelity Sound Lab
Original year:  1973
Format:         FLAC
Encoding:       Lossless
Log:            70%
Directory:      Pink Floyd - Dark Side of the Moon (OMR MFSL 24k Gold Ultradisc II) fixed tags
Size:           219114079
File count:     12
Info hash:      C380B62A3EC6658597C56F45D596E8081B3F7A5C
Uploaded:       2016-11-24 01:34:03
Permalink:      https://redacted.ch/torrents.php?torrentid=1

Comment: |-
  [important]Staff: Technically trumped because EAC 0.95 logs are terrible. There is historic and sentimental value in keeping the first torrent ever uploaded to the site as well as a perfect modern rip. Take no action.[/important]

Files:
- Name: 01 - Speak to Me.flac
  Size: 3732587
- Name: 02 -  Breathe.flac
  Size: 14244409
- Name: 03 - On the Run.flac
  Size: 16541873
- Name: 04 - Time.flac
  Size: 35907465
- Name: 05 -  The Great Gig in the Sky.flac
  Size: 20671913
- Name: 06 - Money.flac
  Size: 37956922
- Name: 07 -Us and Them.flac
  Size: 39706774
- Name: 08 - Any Colour You Like.flac
  Size: 18736396
- Name: 09 - Brain Damage.flac
  Size: 20457034
- Name: 10 - Eclipse.flac
  Size: 11153655
- Name: Pink Floyd - Dark Side of the Moon.CUE
  Size: 1435
- Name: Pink Floyd - Dark Side of the Moon.log
  Size: 3616
~~~

Motivation
----------

Having origin information locally available for each downloaded torrent has a number of benefits:
  * music can be retagged and renamed without losing immediate access to original metadata,
  * if the tracker is ever down or goes away, the origin information is still available, and
  * origin information can be passed to other scripts/tools (e.g., beets) to more accurately identify your music.

While some uploaders helpfully include this information in their uploads, this
is far from standard practice. Additionally, using a tool like `gazelle-origin`
means all torrents will have consistent, parseable origin data independent of
uploader formatting.

Supported Trackers
------------------

Currently, only redacted.ch is supported. Use `--tracker red` or set the `ORIGIN_TRACKER=red` environment variable to
use it.

Installation
------------

Install using `pip`:

    $> pip install git+https://github.com/x1ppy/gazelle-origin

Then add your tracker cookie (see [Obtaining Your Cookie](https://github.com/x1ppy/gazelle-origin#obtaining-your-cookie)) to `~/.bashrc` or equivalent:

    export RED_COOKIE=<your_cookie_here>

Though not required, it's also recommended that you add a default tracker to `~/.bashrc` or equivalent (see [Supported Trackers](#supported-trackers)):

    export ORIGIN_TRACKER=<tracker>

And reload it:

    $> source ~/.bashrc

Obtaining Your Cookie
---------------------
### redacted.ch
`gazelle-origin` requires a browser cookie to log in and make API requests. To obtain your cookie:
* Log in to redacted.ch
* In the same tab, open the browser console:
    * Chrome: Ctrl-Shift-J (Windows) or Command-Option-J (Mac)
    * Firefox: Ctrl-Shift-K (Windows) or Command-Option-K (Mac)
* Select the Network tab and refresh the page
* Select any `.js` or `.php` resource in the list
* In the right pane, scroll down to "cookie" under "Request Headers". Copy
  everything after the `session=`. This your personal cookie (keep it secret!)

Usage
-----

~~~
usage: gazelle-origin [-h] [--out file] [--tracker tracker] id

Fetches torrent origin information from Gazelle-based music trackers

positional arguments:
  id                    torrent identifier, which can be either its info hash, torrent ID, or permalink

optional arguments:
  -h, --help            show this help message and exit
  --out file, -o file   path to write origin data (default: print to stdout)
  --tracker tracker, -t tracker
                        tracker to use

--tracker is optional if the ORIGIN_TRACKER environment variable is set.

If provided, --tracker must be set to one of the following: red
~~~

Examples
--------

These examples all assume you have the `ORIGIN_TRACKER` environment variable set as described in
[Installation](#Installation). If you don't, or if you want to use a different tracker, include the `--tracker` flag in
the following commands.

To show origin information for a given torrent using its info hash:

    $> gazelle-origin C380B62A3EC6658597C56F45D596E8081B3F7A5C

Alternatively, you can pass the permalink instead of the info hash:

    $> gazelle-origin "https://redacted.ch/torrents.php?torrentid=1"

You can even supply just the torrent ID:

    $> gazelle-origin 1

Using `-o file`, you can also specify an output file:

    $> gazelle-origin -o origin.yaml 1

Putting this all together, you can use the following workflow to go through
your existing downloads and populate them with origin.yaml files:

    $> cd /path/to/first/torrent
    $> gazelle-origin -o origin.yaml "https://redacted.ch/torrents.php?torrentid=1"
    $> cd /path/to/another/torrent
    $> gazelle-origin -o origin.yaml "https://redacted.ch/torrents.php?torrentid=2"
    $> ...

Torrent Client Integration
--------------------------

`gazelle-origin` is best used when called automatically in your torrent client when
a download finishes. For example, rTorrent users can add something like the
following to their `~/.rtorrent.rc`:

~~~
method.set_key = event.download.finished,postrun,"execute2={sh,~/postdownload.sh,$d.base_path=,$d.hash=,$session.path=}"
~~~

Then, in `~/postdownload.sh`:
~~~
export RED_COOKIE=<your_cookie_here>

BASE_PATH=$1
INFO_HASH=$2
SESSION_PATH=$3
if [[ $(grep flacsfor.me "$SESSION_PATH"/$INFO_HASH.torrent) ]]; then
    gazelle-origin -t red -o "$BASE_PATH"/origin.yaml $INFO_HASH
fi
~~~

Changelog
---------
### [2.0.2] - 2020-04-11
* Added timeout for requests
### [2.0.1] - 2020-04-10
* Fixed YAML generation bug for fields starting with quotes
### [2.0.0] - 2020-04-08
* Renamed to `gazelle-origin` and switched to YAML output
### [1.0.0] - 2020-03-24
* First tagged release

[2.0.2]: https://github.com/x1ppy/gazelle-origin/compare/2.0.1...2.0.2
[2.0.1]: https://github.com/x1ppy/gazelle-origin/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/x1ppy/gazelle-origin/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/x1ppy/gazelle-origin/releases/tag/1.0.0
