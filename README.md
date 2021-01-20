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
  * origin information can be passed to other scripts/tools (e.g., beets) to more accurately identify your music (see
    [beets integration](#beets)).

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

Then add your tracker API key (see [Obtaining Your API Key](https://github.com/x1ppy/gazelle-origin#obtaining-your-api-key)) to `~/.bashrc` or equivalent:

    export RED_API_KEY=<api_key>

Though not required, it's also recommended that you add a default tracker to `~/.bashrc` or equivalent (see [Supported Trackers](#supported-trackers)):

    export ORIGIN_TRACKER=<tracker>

And reload it:

    $> source ~/.bashrc

Finally, see [Integration](#torrent-clients) for calling `gazelle-origin` automatically from your torrent client.

Obtaining Your API Key
---------------------
`gazelle-origin` requires an API key to make API requests. To obtain your API key:

### redacted.ch
* Go to your profile and select Access Settings on the right side
* Scroll down to API Keys
* Enter "gazelle-origin" as the name
* Uncheck all boxes except Torrents
* Copy all of the text in the Key: box (this is your API key)
* Check Confirm API Key and save

Before saving, the fields should look like this:
![before saving](docs/api-checkboxes.png "Before saving")

After saving, you should see a Torrents API key like this:
![after saving](docs/api-done.png "After saving")

Usage
-----

~~~
usage: gazelle-origin [-h] [--out file] [--tracker tracker] [--env file]
                      [--post file [file ...]] [--recursive] [--no-hash]
                      torrent [torrent ...]

Fetches torrent origin information from Gazelle-based music trackers

positional arguments:
  torrent               torrent identifier, which can be either its info hash,
                        torrent ID, permalink, or path to torrent file(s)
                        whose name or computed info hash should be used

optional arguments:
  -h, --help            show this help message and exit
  --out file, -o file   path to write origin data (default: print to stdout)
  --tracker tracker, -t tracker
                        tracker to use
  --env file, -e file   file to load environment variables from
  --post file [file ...], -p file [file ...]
                        script(s) to run after each output is written. These
                        scripts have access to environment variables with info
                        about the item including OUT, ARTIST, NAME, DIRECTORY,
                        EDITION, YEAR, FORMAT, ENCODING
  --recursive, -r       recursively search directories for files
  --no-hash, -n         don't compute hash from torrent files

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

You can also pass a file or directory. If the file/directory has an info hash in its name that will be used,
or if it is a torrent file its info hash will be computed and used. If a directory is given it will be searched and
each file in it will be looked up as if it were passed as an argument.

    $> gazelle-origin "./Pink Floyd The Wall.torrent"
    $> gazelle-origin ./899350BAF9F3671FE6E0817CBA7B9796E70DD924.torrent
    $> gazelle-origin ./torrents

Using `-o file`, you can specify an output file:

    $> gazelle-origin -o origin.yaml 1

Using `-p file`, you can specify a file to run after each output is saved. This program has access to information
about the downloaded torrent and the output file through environment variables including OUT, ARTIST, NAME, DIRECTORY, EDITION, YEAR, FORMAT, ENCODING.

    $> gazelle-origin -o origin.yaml 1 -p ./post.sh

You can use post scripts to populate your existing library with origin.yaml files using the info hashes of all your snatched torrents.
If all of your torrents are in `./torrents/`, the corresponding data is in `/music/`, and you have a script `./script.sh` containing `mv $OUT "/music/$DIRECTORY/$OUT"`,
then you could run

    $> gazelle-origin -o origin.yaml ./torrents -p ./script.sh

Or you can manually go through your existing downloads and populate them with origin.yaml files:

    $> cd /path/to/first/torrent
    $> gazelle-origin -o origin.yaml "https://redacted.ch/torrents.php?torrentid=1"
    $> cd /path/to/another/torrent
    $> gazelle-origin -o origin.yaml "https://redacted.ch/torrents.php?torrentid=2"
    $> ...

Integration
-----------

### Torrent clients

`gazelle-origin` is best used when called automatically in your torrent client when a download finishes. Use the
following snippets to integrate `gazelle-origin` into your client. If your client isn't listed, please file a PR!

#### rtorrent

`gazelle-origin` is best used when called automatically in your torrent client when
a download finishes. For example, rTorrent users can add something like the
following to their `~/.rtorrent.rc`:

~~~
method.set_key = event.download.finished,postrun,"execute2={sh,~/postdownload.sh,$d.base_path=,$d.hash=,$session.path=}"
~~~

Then, in `~/postdownload.sh`:
~~~
export RED_API_KEY=<api_key>

BASE_PATH=$1
INFO_HASH=$2
SESSION_PATH=$3
if [[ $(grep flacsfor.me "$SESSION_PATH"/$INFO_HASH.torrent) ]]; then
    gazelle-origin -t red -o "$BASE_PATH"/origin.yaml $INFO_HASH
fi
~~~

#### qBittorrent

In Options > Downloads > Run an external program on torrent completion, enter the following:

    gazelle-origin -t %T -o "%R/origin.yaml" --api-key <api_key> %I

To avoid triggering the script for unsupported trackers, an alternative script can be used. Update the file and folder name as necessary:

    bash /config/qb-gazelle-origin.sh "%R" %I %T "%L"

Note that this assumes Python has been added to your environment path. If not and you're a Windows user, you can
fix this by enabling the checkbox at:
_Start > Settings > Apps & Features > Python > Modify > Modify > Next > Add Python to environment variables_.

### beets

Origin files can also be used by beets to significantly improve autotagger results. To do so, install the
[beets-originquery](https://github.com/x1ppy/beets-originquery) plugin, using the following configuration:

~~~
originquery:
    origin_file: origin.yaml
    tag_patterns:
        media: '$.Media'
        year: '$."Edition year"'
        label: '$."Record label"'
        catalognum: '$."Catalog number"'
        albumdisambig: '$.Edition'
~~~

Changelog
---------
### [2.2.1] - 2020-11-16
* Fix URL queries
### [2.2.0] - 2020-11-02
* Add support for multiple inputs, files/directories, env file, and post scripts (thanks @a8f!)
### [2.1.1] - 2020-04-27
* Accept any string containing "flacsfor.me" as RED tracker ID
### [2.1.0] - 2020-04-27
* Added `--api-key` to allow specifying API key on execution
* Accept "flacsfor.me" as a RED tracker ID
* More sane package organization
### [2.0.4] - 2020-04-18
* Fixed YAML generation for comments containing whitespace-only lines
### [2.0.3] - 2020-04-13
* Replaced cookie with API key
### [2.0.2] - 2020-04-11
* Added timeout for requests
### [2.0.1] - 2020-04-10
* Fixed YAML generation bug for fields starting with quotes
### [2.0.0] - 2020-04-08
* Renamed to `gazelle-origin` and switched to YAML output
### [1.0.0] - 2020-03-24
* First tagged release

[2.2.1]: https://github.com/x1ppy/gazelle-origin/compare/2.2.0...2.2.1
[2.2.0]: https://github.com/x1ppy/gazelle-origin/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/x1ppy/gazelle-origin/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/x1ppy/gazelle-origin/compare/2.0.4...2.1.0
[2.0.4]: https://github.com/x1ppy/gazelle-origin/compare/2.0.3...2.0.4
[2.0.3]: https://github.com/x1ppy/gazelle-origin/compare/2.0.2...2.0.3
[2.0.2]: https://github.com/x1ppy/gazelle-origin/compare/2.0.1...2.0.2
[2.0.1]: https://github.com/x1ppy/gazelle-origin/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/x1ppy/gazelle-origin/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/x1ppy/gazelle-origin/releases/tag/1.0.0
