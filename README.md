OpenWPM [![Build Status](https://travis-ci.org/citp/OpenWPM.svg)](https://travis-ci.org/citp/OpenWPM)
=======

OpenWPM is a web privacy measurement framework which makes it easy to collect
data for privacy studies on a scale of thousands to millions of site. OpenWPM
is built on top of Firefox, with automation provided by Selenium. It includes
several hooks for data collection, including a proxy, a Firefox extension, and
access to Flash cookies. Check out the instrumentation section below for more
details.

Installation
------------

OpenWPM has been developed and tested on Ubuntu 14.04. An installation script,
`install.sh` is included to install both the system and python dependencies
automatically. A few of the python dependencies require specific versions, so
you should install the dependencies in a virtual environment if you're
installing a shared machine.

It is likely that OpenWPM will also work on Mac OSX, however this has not been
tested. If you have experience running OpenWPM on other platforms, please let
us know!

Quick Start
-----------

Once installed, it's very easy to run a quick test of OpenWPM. Check out
`demo.py` for an example. This will the default setting specified in
`automation/default_manager_params.json` and
`automation/default_browser_params.json`, with the exception of the changes
specified in `demo.py`.

You can test other configurations by changing the values in these two
dictionaries. `manager_params` is meant to specify the platform-wide settings,
while `browser_params` specifies browser-specific settings (and as such
defaults to a `list` of settings, of length equal to the number of browsers you
are using. We are currently working on full documentation of these settings.

The [wiki](https://github.com/citp/OpenWPM/wiki) provides a more in-depth
tutorial, however it is currently out of date. In particular you can find
[advanced features](https://github.com/citp/OpenWPM/wiki/Advanced-Features),
and [additional
commands](https://github.com/citp/OpenWPM/wiki/Available-Commands).
You can also take a look at two of our past studies (1) and (2),  which use the
infrastructure.

(1) [The Web Never Forgets](https://github.com/citp/TheWebNeverForgets)
(2) [Cookies that Give You Away](https://github.com/englehardt/cookies-that-give-you-away)

Instrumentation
---------------

OpenWPM includes the following instrumentation by default:

* An HTTP Proxy (mitmproxy)
    * HTTP Requests and Responses
    * Parsing of HTTP Request and Response Cookies
        * NOTE: this will not include cookies set by Javascript, see our
            Firefox extension option below.
    * De-duplicated content storage
        * Right now we detect and store javascript, but this can be expanded
* A Firefox Extension
    * Javascript calls
    * Cookie setting and access
* Disk Scans
    * Flash cookie setting
    * Cookie access

Data Format
-----------

OpenWPM saves crawl data in several outputs. The bulk of the data is stored
in a SQLite database, but additional data may be stored in locations detailed
below.

* HTTP, Cookie, Javascript calls, and meta-data
    * SQLite database specified by `manager_params['database_name']`.
    * Schema specified by: `automation/schema.sql`, instrumentation may specify
        additional tables necessary for their measurements.
* Javascript files
    * Collected when `browser_params['save_javascript'] = True`
    * Javascript files are stored in `javascript.ldb`. The location of this
        database is specified by `manager_params['data_directory']`.
    * The files are stored with `zlib` compression by the hash of the
        uncompressed content.
    * The files are stored in a `LevelDB` database, accessed with `plyvel`.
    * This hash is used to reference the scripts from the SQLite database, for
        example the `content_hash` column of HTTP Responses.
* Log Files
    * Stored in the directory specified by `manager_params['data_directory']`.
    * Name specified by `manager_params['log_file']`.
* Browser Profile
    * Contains cookies, Flash objects, and so on that are dumped after a crawl
        is finished
    * Dumped to the location specified in `dump_profile` command.

The database is keyed by the crawler ID and the `top_url` being visited (the
url typed into the browser address bar).

Disclaimer
-----------

Note that OpenWPM is under active development, and should be considered
experimental software. The repository may contain experimental features that
aren't fully tested. We recommend using a [tagged
release](https://github.com/citp/OpenWPM/releases).

Although OpenWPM is actively used by our group for research studies and we
regularly use of the data collected, it is still possible there are unknown bugs
in the infrastructure. We are in the process of writing comprehensive tests to
verify the integrity of all included instrumentation. Prior to using OpenWPM
for your own research we encourage you to write tests (and submit pull
requests!) for any instrumentation that isn't currently included in our test
scripts.

Citation
--------

If you use OpenWPM in your research, please cite our current [Technical
Report](http://randomwalker.info/publications/OpenWPM_1_million_site_tracking_measurement.pdf) on the
infrastructure. You can use the following BibTeX.

    @unpublished{englehardt2015census,
        author = "Steven Englehardt and Arvind Narayanan",
        title  = "{Online tracking: A 1-million-site measurement and analysis}",
        month = may,
        year   = "2016",
        note = "[Technical Report]"
    }

License
-------

OpenWPM is licensed under GNU GPLv3. Additional code has been included from
[FourthParty](https://github.com/fourthparty/fourthparty) and
[Privacy Badger](https://github.com/EFForg/privacybadgerfirefox), both of which 
are licensed GPLv3+.
