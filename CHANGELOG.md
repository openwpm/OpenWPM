# Changelog


## v0.12.0 - 2020-08-26

Firefox 80.0.0 release

There have been no new features added in this release.
However there are two significant bugfixes worth highlighting:

- We hopefully fixed [a bug when hashing content](https://github.com/mozilla/OpenWPM/issues/711) where the same file could have multiple hashes
  If you ran a big crawl and could repeat @birdsarah's analysis, we'd be grateful if you reported your results [here](https://github.com/mozilla/OpenWPM/issues/719)
- Fixed longstanding bug when [propagating exceptions from the BrowserManager to the TaskManager](https://github.com/mozilla/OpenWPM/issues/547) you should now be seeing
  the exception that happened in the BrowserManager in your logs

__NOTE:__ Please be aware that this release contains a regression related to https://bugzilla.mozilla.org/show_bug.cgi?id=1656405 and https://bugzilla.mozilla.org/show_bug.cgi?id=1599160.
This means some requests with cached responses might not show up as requests or responses in your instrumentation. We assume this will be fixed in FF81.

## v0.11.0 - 2020-07-08

Firefox 78.0.1 scheduled release. This release contains some minor bug fixes
and one new feature: Arbitrary JS Instrumentation.

New features:
  * Arbitrary JS Instrumentation allows users to specify, python side the set
    APIs they would like to instrument in their crawl. The default remains the
    set of fingerprinting apis, now called ``collection_fingerprinting``. This has
    meant a number of API changes including the renaming of the browser_param
    ``js_instrument_modules`` to ``js_instrument_settings``. As
    ``js_instrument_modules`` was not actually configurable previously, we do not
    anticipate too much disruption to users. Details of how to configure the
    new ``js_instrument_settings`` are in the
    [Instrumentation and Data Access section of the README](./README.md#instrumentation-and-data-access).

    - [Issue 641](https://github.com/mozilla/OpenWPM/issues/641)
    - [PR 642](https://github.com/mozilla/OpenWPM/pull/642)

Minor fixes:
  * Asserting that unpickled exception is an exception [PR 705](https://github.com/mozilla/OpenWPM/pull/705)
  * Minor fixes [PR 703](https://github.com/mozilla/OpenWPM/pull/703)
  * Better crawling experience [PR 696](https://github.com/mozilla/OpenWPM/pull/696)

No OpenWPM release was made with Firefox 78.0.

## v0.10.0 - 2020-06-11

This release is a long overdue release of OpenWPM, and contains too many
changes to list here. Instead, we highlight the major architectural since the
previous release. The instrumentation has been completely rewritten as part of
this release to the new WebExtensions framework. Older versions of OpenWPM
should not be used.

Changes:
  * Migrate instrumentation from the addon-sdk framework to WebExtensions.
  * Migrate to unbranded builds of Firefox, and off of the ESR channel to the
    Release channel
  * Add support for MacOS development
  * Add an S3Aggregator that saves data in Parquet format on S3
  * Use conda for dependency management
  * Disable stateful crawling due to intermittent loss of profiles and
    geckodriver incompatibilities
  * Refactor extension instumentation to live in a separate module
  * Re-write logger and add support for logging to sentry
  * Add a crawler.py crawl script that can be used for cloud deployments like
    the type documented in https://github.com/mozilla/openwpm-crawler
  * Add support for Firefox's native headless mode alongside XVFB
  * Add Dockerfile and automatically deploy builds to dockerhub
  * Add a Navigation instrument that records navigation events
  * Drop support for Python 2
  * Remove support for Flash
  * Numerous stability and data saving improvements (particularly for cloud
    crawls / the S3Aggregator)
  * Numerous bugfixes + improved testing

## v0.9.0 - 2019-04-15

A checkpoint release for the final version of OpenWPM to support Firefox 52
and the addon-sdk framework. We recommend against using this release as Firefox
52ESR is no longer receiving security updates.

Changes:
  * The ``automation`` library can now be used with Python 3.4 or later,
    as well as Python 2.7.
  * Bump to Firefox 52 ESR, Selenium 3.4.0+, and geckodriver 0.15.0.
    * geckodriver is required for Selenium 3+. ``install.sh`` will download
      and install it.
    * geckodriver 0.16.0+ does not support Firefox 52 or lower, so we are
      stuck with 0.15.0 (and any bugs it may have) until the next ESR release.
    * These versions of geckodriver and Selenium require Firefox 48+.
  * MITMProxy support has been removed.  Use ``http_instrument`` instead.
  * Bundled Firefox privacy extensions have been updated.
    * AdBlock Plus support has been removed.
    * uBlock Origin and Disconnect added.
    * Ghostery has been updated.
  * Extensions built using the WebExtensions API are now supported. Our
    extension still uses the add-on sdk.
  * Experimental support for saving Parquet files on S3
  * Numerous bug fixes

## v0.8.0 - 2017-10-09

A long overdue version bump to checkpoint the final version to support
Selenium 2 + FF 45. Note we recommend against using the release as Firefox
45ESR is no longer receiving security patches.

Changes:
  * Add extension-based HTTP instrumentation, including POST body processing
  * Deprecate proxy-based HTTP instrumentation
  * Save stacktrace of HTTP requests
  * Prevent Selenium 2 from self identifying in the DOM
  * Add support for blocking commands
  * Improve exception handling in child processes
  * Refactor of socket interface in extension
  * Improvements to manual testing code
  * Add a logging module to the extension, logs to central log file
  * Instrument ``document.cookie``
  * A number of improvements to the ``instrumentObject`` instrumentation
    interface in extension
  * Make ``install.sh`` scriptable

## v0.7.0 - 2016-11-15

Changes:
  * Bugfixes to extension instrumentation where records would be dropped when
    the extension was under heavy load and fail to re-enable until the browser
    was restarted.
  * Bugfix to extension / socket interface
  * Add ``run_custom_function`` command
  * Using alternative serialization/parallelization with ``dill`` and
    ``multiprocess``
  * Better documentation
  * Bugfixes to install script
  * Add ``save_screenshot`` and ``dump_page_source`` commands
  * Add Audio API instrumentation
  * Bugfix to ``browse`` command
  * Bugfix to extension instrumentation injection to avoid Security Errors

## v0.6.2 - 2016-04-08

Changes:
  * Bugfix to browse command. Now supports sleeping after get.

## v0.6.1 - 2016-04-08

Critical:
  * Bugfix in LevelDBAggregator preventing data loss

Changes:
  * Bump to Firefox 45 & Selenium 2.53.0
  * Update certificate stored
  * Added sleep argument to ``get`` command
  * Added install script for development dependencies
  * Improved error handling in TaskManager and Proxy
  * Version bumps and bugfixes in HTTPS Everywhere, Ghostery, and ABP
  * Tests added!
  * Numerous bugfixes and improvements in Javascript Instrumentation

## v0.6.0 - 2015-12-22

Changes:
  * Cleanup of Firefox prefs to make browsers faster and reduce phoning home
  * Use LevelDB for javascript file storage
  * Improved HTTP Cookie Parsing
  * Several bugfixes to extension instrumentation
  * Improved profile handling during shutdown and crashes
  * Improved handling of child Exceptions
  * Inital platform tests
  * Improvements to javascript instrumentation

## v0.5.1 - 2015-10-15

Changes:
  * Save json serialized headers and fix cookie parsing

## v0.5.0 - 2015-10-14

Changes:
  * Added support for saving all javascript files de-duplicated and compressed
  * Created two configuration dictionaries. One for individual browsers and
    another for the entire infrastructure
  * Support for using OpenWPM as a submodule
  * Firefox (v39) and Selenium (v2.47.1)
  * Added support for launching Ghostery, HTTPS Everywhere, and AdBlock Plus
  * Removed Random Extension Support
  * Bugfix for broken profile saving.
  * Bugfix for profile clearing when memory limits are exceeded
  * Numerous stability fixes
  * Full Logging support in all commands

## v0.4.0

Changes:
  * Significant stability improvements for long crawls
  * Support for logging with logging module
  * A large number of bugfixes related to process handling
  * Prevention of a large number of stray tmp files/folders during long crawls
  * Process/memory watchdog to handle orphaned processes and keep memory usage
    reasonable
  * Numerous bugfixes for extension
  * Failure thresholds to prevent infinite loops of browser respawns or
    command execution attempts (instead, Errors and raised)
  * Script to install dependencies
  * API changes to command timeouts
  * Move SocketInterface from pickle to json serialization

Known Issues:
  * Encoding issues cause a very small percentage of data to be dropped by the
    extension
  * Malformed queries are occassionally sent to the DataAggregator and are
    dropped. The cause is unknown.
  * Forking can be done in a more memory efficient way


## Older releases

* 0.3.1 - Fixes #5
* 0.3.0 - Experimental merge of Fourthparty + framework to allow additional
        javascript instrumentation.
* 0.2.3 - Timeout logging
* 0.2.2 - Browse command + better scrolling + bugfixes
* 0.2.1 - Support for MITMProxy v0.11 + minor bugfixes
* 0.2.0 - Complete re-write of HTTP Cookie parsing
* 0.1.1 - Simplfied load of default settings, including wiki demo
* 0.1.0 - Initial Public Release
