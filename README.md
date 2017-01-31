OpenWPM [![Build Status](https://travis-ci.org/citp/OpenWPM.svg?branch=master)](https://travis-ci.org/citp/OpenWPM)
=======

OpenWPM is a web privacy measurement framework which makes it easy to collect
data for privacy studies on a scale of thousands to millions of site. OpenWPM
is built on top of Firefox, with automation provided by Selenium. It includes
several hooks for data collection, including a proxy, a Firefox extension, and
access to Flash cookies. Check out the instrumentation section below for more
details.

Installation
------------

OpenWPM has been developed and tested on Ubuntu 14.04/16.04. An installation
script, `install.sh` is included to install both the system and python
dependencies automatically. A few of the python dependencies require specific
versions, so you should install the dependencies in a virtual environment if
you're installing a shared machine. If you plan to develop OpenWPM's
instrumentation extension or run tests you will also need to install the
development dependencies included in `install-dev.sh`.

It is likely that OpenWPM will also work on Mac OSX, however this has not been
tested. If you have experience running OpenWPM on other platforms, please let
us know!

Quick Start
-----------

Once installed, it is very easy to run a quick test of OpenWPM. Check out
`demo.py` for an example. This will use the default setting specified in
`automation/default_manager_params.json` and
`automation/default_browser_params.json`, with the exception of the changes
specified in `demo.py`.

More information on the instrumentation and configuration parameters is given
below.


The [wiki](https://github.com/citp/OpenWPM/wiki) provides a more in-depth
tutorial, including a
[platform demo](https://github.com/citp/OpenWPM/wiki/Platform-Demo)
and a description of the
[additional commands](https://github.com/citp/OpenWPM/wiki/Available-Commands)
available. You can also take a look at two of our past studies, which use the
infrastructure:

1. [The Web Never Forgets](https://github.com/citp/TheWebNeverForgets)
2. [Cookies that Give You Away](https://github.com/englehardt/cookies-that-give-you-away)

Instrumentation and Data Access
-------------------------------

OpenWPM provides several instrumentation modules which can be enabled
independently of each other for each crawl. With the exception of Javascript
response body content, all instrumentation saves to a SQLite database specified
by `manager_params['database_name']` in the main output directory. Javascript
bodies are saved to `javascript.ldb`. The SQLite schema specified by:
`automation/schema.sql`, instrumentation may specify additional tables necessary
for their measurement data (see
[extension tables](https://github.com/citp/OpenWPM/tree/master/automation/Extension/firefox/data)).

* HTTP Request and Response Headers, POST request bodies
    * Set `browser_params['http_instrument'] = True`
    * Data is saved to the `http_requests` and `http_responses` tables.
    * OCSP POST request bodies are not recorded
    * Note: request and response headers for cached content are also saved,
        with the exception of images.
        See: [Bug 634073](https://bugzilla.mozilla.org/show_bug.cgi?id=634073).
* Javascript Calls
    * Records all method calls (with arguments) and property accesses for APIs
      of potential fingerprinting interest:
        * HTML5 Canvas
        * HTML5 WebRTC
        * HTML5 Audio
        * Plugin access (via `navigator.plugins`)
        * MIMEType access (via `navigator.mimeTypes`)
        * `window.Storage`, `window.localStorage`, `window.sessionStorage`,
              and `window.name` access.
        * Navigator properties (e.g. `appCodeName`, `oscpu`, `userAgent`, ...)
        * Window properties (via `window.screen`)
    * Set `browser_params['js_instrument'] = True`
    * Data is saved to the `javascript` table.
* Javascript Files
    * Saves all Javascript files encountered during the crawl to a `LevelDB`
        database de-duplicated by the md5 hash of the content.
    * Set `browser_params['save_javascript'] = True`
    * The `content_hash` column of the `http_responses` table contains the md5
        hash for each script, and can be used to do content lookups in the
        LevelDB content database.
    * This instrumentation can be easily expanded to other content types.
* Flash Cookies
    * Recorded by scanning the respective Flash directories after each page visit.
    * To enable: call the `CommandSequence::dump_flash_cookies` command after
        a page visit. Note that calling this command will close the current tab
        before recording the cookie changes.
    * Data is saved to the `flash_cookies` table.
    * NOTE: Flash cookies are shared across browsers, so this instrumentation
        will not correctly attribute flash cookie changes if more than 1
        browser is running on the machine.
* Cookie Access (*Experimental* -- Needs tests)
    * Set `browser_params['cookie_instrument'] = True`
    * Data is saved to the `javascript_cookies` table.
    * Will record cookies set both by Javascript and via HTTP Responses
* Content Policy Calls (*Experimental* -- Needs tests)
    * Set `browser_params['cp_instrument'] = True`
    * Data is saved to the `content_policy` table.
    * Provides additional information about what caused a request and what it's for
    * NOTE: This instrumentation is largely unchanged since it was ported from
        [FourthParty](https://github.com/fourthparty/fourthparty), and is not
        linked to any other instrumentation tables.
* Cookie Access (Alternate)
    * Recorded by scanning the `cookies.sqlite` database in the Firefox profile
        directory.
    * Should contain both cookies added by Javascript and by HTTP Responses
    * To enable: call the `CommandSequence::dump_profile_cookies` command after
        a page visit. Note that calling this command will close the current tab
        before recording the cookie changes.
    * Data is saved to the `profile_cookies` table
* Log Files
    * Stored in the directory specified by `manager_params['data_directory']`.
    * Name specified by `manager_params['log_file']`.
* Browser Profile
    * Contains cookies, Flash objects, and so on that are dumped after a crawl
        is finished
    * Automatically saved when the platform closes or crashes by specifying
        `browser_params['profile_archive_dir']`.
    * Save on-demand with the `CommandSequence::dump_profile` command.
* **DEPRECATED** HTTP Request and Response Headers via mitmproxy
    * This will be removed in future releases
    * Set `browser_params['proxy'] = True`
    * Data is saved to the `http_requests_proxy` and `http_responses_proxy`
        tables.
    * Saves both HTTP and HTTPS request and response headers
    * Several drawbacks:
        * Cached requests and responses are missed entirely (See #71)
        * Some HTTPS connections fail with certificate warnings (See #53)
        * The mitmproxy version used (v0.13) is a few releases behind the
            current mitmproxy library and will likely continue to have more
            issues unless updated.
        * Has significantly less context available around a request/response
            than is available from within the browser.
* **DEPRECATED** Javascript Response Bodies via mitmproxy
    * This will be removed in future releases
    * Set `browser_params['save_javascript_proxy'] = True`
    * Saves javascript response bodies to a LevelDB database de-duplicated by
        the murmurhash3 of the content. `content_hash` in `http_response_proxy`
        keys into this content database.
    * NOTE: In addition to the other drawbacks of proxy-based measurements,
        content must be decoded before saving and not all current encodings are
        supported. In particular, brotli (`br`) is not supported.
* **DEPRECATED** HTTP Request and Response Cookies via mitmproxy
    * This will be removed in future releases
    * Derived post-crawl from proxy-based HTTP instrumentation
    * To enable: call
      `python automation/utilities/build_cookie_table.py <sqlite_database>`.
    * Data is saved to the `http_request_cookies_proxy` and
        `http_response_cookies_proxy` tables.
    * Several drawbacks:
        * Will not detect cookies set via Javascript, but will still record
            when those cookies are sent with requests.
        * Cookie parsing is done using a custom `Cookie.py` module. Although a
            significant effort went into replicating Firefox's cookie parsing,
            it may not be a faithful reproduction.

Browser and Platform Configuration
----------------------------------

The browser and platform can be configured by two separate dictionaries. The
platform configuration options can be set in `manager_params`, while the
browser configuration options can be set in `browser_params`. The default
settings are given in `automation/default_manager_params.json` and
`automation/default_browser_params.json`.

To load the default configuration parameter dictionaries we provide a helper
function `TaskManager::load_default_params`. For example:

```python
from automation import TaskManager
manager_params, browser_params = TaskManager.load_default_params(num_browsers=5)
```

where `manager_params` is a dictionary and `browser_params` is a length 5 list
of configuration dictionaries.

### Platform Configuration Options

* `data_directory`
  * The directory in which to output the crawl database and related files. The
    directory given will be created if it does not exist.
* `log_directory`
  * The directory in which to output platform logs. The
    directory given will be created if it does not exist.
* `log_file`
  * The name of the log file to be written to `log_directory`.
* `database_name`
  * The name of the database file to be written to `data_directory`
* `failure_limit`
  * The number of successive command failures the platform will tolerate before
    raising a `CommandExecutionError` exception. Otherwise the default is set
    to 2 x the number of browsers plus 10.
* `testing`
  * A platform wide flag that can be used to only run certain functionality
    while testing. For example, the Javascript instrumentation
    [exposes its instrumentation function](https://github.com/citp/OpenWPM/blob/91751831647c37b769f0039d99d0a164384c76ae/automation/Extension/firefox/data/content.js#L447-L449)
    on the page script global to allow test scripts to instrument objects
    on-the-fly. Depending on where you would like to add test functionality,
    you may need to propagate the flag.
  * This is not something you should enable during normal crawls.

### Browser Configuration Options

Note: Instrumentation configuration options are described in the
*Instrumentation and Data Access* section and profile configuration options are
described in the *Browser Profile Support* section. As such, these options are
left out of this section.

* `disable_webdriver_self_id`
  * Prevents Selenium from identifying itself in the DOM. See
    [Issue #91](https://github.com/citp/OpenWPM/issues/91).
* `bot_mitigation`
  * Performs some actions to prevent the platform from being detected as a bot.
  * Note, these aren't comprehensive and automated interaction with the site
    will still appear very bot-like.
* `disable_flash`
  * Flash is disabled by default. Set this to `False` to re-enable. Note that
    flash cookies are shared between browsers.
* `headless`
  * Launch the browser in a virtual frame buffer, no GUI will be visible.
  * Use this when running browsers on a remote machine or to run crawls in the
      background on a local machine.
* `browser`
  * Used to specify which browser to launch. Currently only `firefox` is
    supported.
  * Other browsers may be added in the future.
* `tp_cookies`
  * Specifies the third-party cookie policy to set in Firefox.
  * The following options are supported:
    * `always`: Accept all third-party cookies
    * `never`: Never accept any third-party cookies
    * `from_visited`: Only accept third-party cookies from sites that have been
      visited as a first party.
* `donottrack`
  * Set to `True` to enable Do Not Track in the browser.
* `ghostery`
  * Set to `True` to enable Ghostery with all blocking enabled
  * NOTE: The Ghostery version used (including filter lists) may be outdated.
    It's recommended that you update the xpi and `store.json` file (included in
    the extension profile directory). These can be placed
    [here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions/ghostery)
* `https-everywhere`
  * Set to `True` to enable HTTPS Everywhere in the browser.
  * NOTE: The HTTPS Everywhere version may be outdated. It's recommended you
    update the xpi
    [located here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions)
    before crawling.
* `adblock-plus`
  * Set to `True` to enable AdBlock Plus in the browser.
  * The filter lists should be automatically downloaded and installed, but the
    xpi, [located here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions)
    , might be outdated.
  * NOTE: There is a known issue of AdBlock Plus not blocking all resources
    on the first page visit. See
    [Issue #35](https://github.com/citp/OpenWPM/issues/35)
    for more information.
* **NOT SUPPORTED** ` tracking-protection`
  * Set to `True` to enable Firefox's built-in
    [Tracking Protection](https://developer.mozilla.org/en-US/Firefox/Privacy/Tracking_Protection).
  * NOTE: This is not currently supported. See
    [Issue #101](https://github.com/citp/OpenWPM/issues/101) for more
    information.

Browser Profile Support
-----------------------

### Stateful vs Stateless crawls

By default OpenWPM performs a "stateful" crawl, in that it keeps a consistent
browser profile between page visits in the same browser. If the browser
freezes or crashes during the crawl, the profile is saved to disk and restored
before the next page visit.

It's also possible to run "stateless" crawls, in which each new page visit uses
a fresh browser profile. To perform a stateless crawl you can restart the
browser after each command sequence by setting the `reset` initialization
argument to `True` when creating the command sequence. As an example:

```python
manager = TaskManager.TaskManager(manager_params, browser_params)

for site in sites:
    command_sequence = CommandSequence.CommandSequence(site, reset=True)
    command_sequence.get(sleep=30, timeout=60)
    command_sequence.dump_profile_cookies(120)
    manager.execute_command_sequence(command_sequence)
```

In this example, the browser will `get` the requested `site`, sleep for 30
seconds, dump the profile cookies to the crawl database, and then restart the
browser before visiting the next `site` in `sites`.

### Loading and saving a browser profile

It's possible to load and save profiles during stateful crawls. Profile dumps
currently consist of the following browser storage items:

* cookies
* localStorage
* IndexedDB
* browser history

Other browser state, such as the browser cache, is not saved. In
[Issue #62](https://github.com/citp/OpenWPM/issues/62) we plan to expand
profiles to include all browser storage.

#### Save a profile

A browser's profile can be saved to disk for use in later crawls. This can be
done using a browser command or by setting a browser configuration parameter.
For long running crawls we recommend saving the profile using the browser
configuration parameter as the platform will take steps to save the
profile in the event of a platform-level crash, whereas there is no guarantee
the browser command will run before a crash.

**Browser configuration parameter:** Set the `profile_archive_dir` browser
parameter to a directory where the browser profile should be saved. The profile
will be automatically saved when `TaskManager::close` is called or when a
platform-level crash occurs.

**Browser command:** See the command definition
[wiki page](https://github.com/citp/OpenWPM/wiki/Available-Commands#dump_profile)
for more information.

#### Load a profile

To load a profile, specify the `profile_tar` browser parameter in the browser
configuration dictionary. This should point to the location of the
`profile.tar` or (`profile.tar.gz` if compressed) file produced by OpenWPM.
The profile will be automatically extracted and loaded into the browser
instance for which the configuration parameter was set.

Development pointers
--------------------

Much of OpenWPM's instrumentation is included in a Firefox add-on SDK extension.
Thus, in order to add or change instrumentation you will need a few additional
dependencies, which can be installed with `install-dev.sh`.

### Editing instrumentation

The extension instrumentation is included in `/automation/Extension/firefox/`.
Any edits within this directory will require the extension to be re-built with
`jpm` to produce a new `openwpm.xpi` with your updates. For more information on
developing a Firefox extension, we recommend reading this
[MDN introductory tutorial](https://developer.mozilla.org/en-US/Add-ons/SDK/Tutorials/Getting_Started_(jpm)),
 as well as the [jpm reference page](https://developer.mozilla.org/en-US/Add-ons/SDK/Tools/jpm).


### Running tests

OpenWPM's tests are build on `py.test`. To run the tests you will need a few
additional dependencies, which can be installed by running `install-dev.sh`.

Once installed, execute `py.test -vv` in the test directory to run all tests.


Troubleshooting
---------------

1. `IOError: [Errno 2] No such file or directory: '../../firefox-bin/application.ini'`

  This error occurs when the platform can't find a standalone Firefox binary in
  the root directory of OpenWPM. The `install.sh` script will download and unzip
  the appropriate version of Firefox for you. If you've run this script but still
  don't have the binary installed note that the script will exit if any command
  fails, so re-run the install script checking that no command fails.

2. `WebDriverException: Message: The browser appears to have exited before we could connect...`

  This error indicates that Firefox exited during startup (or was prevented from
  starting). There are many possible causes of this error:

  * If you are seeing this error for all browser spawn attempts check that:
    * Both selenium and Firefox are the appropriate versions. Run the following
      commands and check that the versions output match the required versions in
      `install.sh` and `requirements.txt`. If not, re-run the install script.
      ```sh
      cd firefox-bin/
      firefox --version
      ```

      and

      ```sh
        pip show selenium
      ```
    * If you are running in a headless environment (e.g. a remote server), ensure
      that all browsers have the `headless` browser parameter set to `True` before
      launching.
  * If you are seeing this error randomly during crawls it can be caused by
    an overtaxed system, either memory or CPU usage. Try lowering the number of
    concurrent browsers.


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

If you use OpenWPM in your research, please cite our CCS 2016 [publication](http://randomwalker.info/publications/OpenWPM_1_million_site_tracking_measurement.pdf)
on the infrastructure. You can use the following BibTeX.

    @inproceedings{englehardt2016census,
        author    = "Steven Englehardt and Arvind Narayanan",
        title     = "{Online tracking: A 1-million-site measurement and analysis}",
        booktitle = {Proceedings of ACM CCS 2016},
        year      = "2016",
    }

License
-------

OpenWPM is licensed under GNU GPLv3. Additional code has been included from
[FourthParty](https://github.com/fourthparty/fourthparty) and
[Privacy Badger](https://github.com/EFForg/privacybadgerfirefox), both of which
are licensed GPLv3+.
