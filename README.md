
OpenWPM
[![Build Status](https://travis-ci.org/mozilla/OpenWPM.svg?branch=master)](https://travis-ci.org/mozilla/OpenWPM)
[![OpenWPM Matrix Channel](https://img.shields.io/matrix/OpenWPM:mozilla.org?label=Join%20us%20on%20matrix&server_fqdn=mozilla.modular.im)](https://matrix.to/#/!pFJihVSEWzcMCcOzSH:mozilla.org?via=mozilla.org) <!-- omit in toc -->
=======

OpenWPM is a web privacy measurement framework which makes it easy to
collect data for privacy studies on a scale of thousands to millions
of websites. OpenWPM is built on top of Firefox, with automation provided
by Selenium. It includes several hooks for data collection. Check out
the instrumentation section below for more details.

Table of Contents <!-- omit in toc -->
------------------

* [Installation](#installation)
* [Quick Start](#quick-start)
* [Instrumentation and Data Access](#instrumentation-and-data-access)
* [Output Format](#output-format)
    * [Local Databases](#local-databases)
    * [Parquet on Amazon S3 **Experimental**](#parquet-on-amazon-s3-experimental)
* [Browser and Platform Configuration](#browser-and-platform-configuration)
  * [Platform Configuration Options](#platform-configuration-options)
  * [Browser Configuration Options](#browser-configuration-options)
* [Browser Profile Support](#browser-profile-support)
  * [Stateful vs Stateless crawls](#stateful-vs-stateless-crawls)
  * [Loading and saving a browser profile](#loading-and-saving-a-browser-profile)
    * [Save a profile](#save-a-profile)
    * [Load a profile](#load-a-profile)
* [Development pointers](#development-pointers)
  * [Types Annotations in Python](#types-annotations-in-python)
  * [Editing instrumentation](#editing-instrumentation)
  * [Debugging the platform](#debugging-the-platform)
  * [Managing requirements](#managing-requirements)
  * [Running tests](#running-tests)
  * [Mac OSX (Limited support for developers)](#mac-osx-limited-support-for-developers)
* [Troubleshooting](#troubleshooting)
* [Docker Deployment for OpenWPM](#docker-deployment-for-openwpm)
  * [Building the Docker Container](#building-the-docker-container)
  * [Running Measurements from inside the Container](#running-measurements-from-inside-the-container)
  * [MacOS GUI applications in Docker](#macos-gui-applications-in-docker)
* [Disclaimer](#disclaimer)
* [Citation](#citation)
* [License](#license)


Installation
------------

OpenWPM is a Python >3.6 application developed and tested for Ubuntu 18.04.
Python 2 is not supported. An installation
script, `install.sh` is included to install both the system and python
dependencies automatically. A few of the python dependencies require specific
versions, so you should install the dependencies in a virtual environment if
you're installing a shared machine. If you plan to develop OpenWPM's
instrumentation extension or run tests you will also need to install the
development dependencies included in `install-dev.sh`.

It is likely that OpenWPM will work on platforms other than Ubuntu, however
we do not officially support anything else. For pointers on alternative
platform support see
[the wiki](https://github.com/citp/OpenWPM/wiki/OpenWPM-on-Alternate-Platforms).

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
independently of each other for each crawl. More detail on the output is
available [below](#output-format).

* HTTP Request and Response Headers, redirects, and POST request bodies
    * Set `browser_params['http_instrument'] = True`
    * Data is saved to the `http_requests`, `http_responses`, and
        `http_redirects`  tables.
        * `http_requests` schema
            [documentation](https://github.com/citp/OpenWPM/wiki/Instrumentation-Schema-Documentation#http-requests)
        * `channel_id` can be used to link a request saved in the
            `http_requests` table to its corresponding response in the
            `http_responses` table.
        * `channel_id` can also be used to link a request to the subsequent
            request that results after an HTTP redirect (3XX response). Use the
            `http_redirects` table, which includes a mapping between
            `old_channel_id`, the `channel_id` of the HTTP request that
            resulted in a 3XX response, and `new_channel_id`, the HTTP request
            that resulted from that redirect.
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
* Response body content
    * Saves all files encountered during the crawl to a `LevelDB`
        database de-duplicated by the md5 hash of the content.
    * Set `browser_params['save_content'] = True`
    * The `content_hash` column of the `http_responses` table contains the md5
        hash for each script, and can be used to do content lookups in the
        LevelDB content database.
    * NOTE: this instrumentation may lead to performance issues when a large
        number of browsers are in use.
    * Set `browser_params['save_content']` to a comma-separated list of
        [resource_types](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType)
        to save only specific types of files, for instance
        `browser_params['save_content'] = "script"` to save only Javascript
        files. This will lessen the performance impact of this instrumentation
        when a large number of browsers are used in parallel.
* Flash Cookies
    * Recorded by scanning the respective Flash directories after each page visit.
    * To enable: call the `CommandSequence::dump_flash_cookies` command after
        a page visit. Note that calling this command will close the current tab
        before recording the cookie changes.
    * Data is saved to the `flash_cookies` table.
    * NOTE: Flash cookies are shared across browsers, so this instrumentation
        will not correctly attribute flash cookie changes if more than 1
        browser is running on the machine.
* Cookie Access
    * Set `browser_params['cookie_instrument'] = True`
    * Data is saved to the `javascript_cookies` table.
    * Will record cookies set both by Javascript and via HTTP Responses
* Log Files
    * Stored in the directory specified by `manager_params['data_directory']`.
    * Name specified by `manager_params['log_file']`.
* Browser Profile
    * Contains cookies, Flash objects, and so on that are dumped after a crawl
        is finished
    * Automatically saved when the platform closes or crashes by specifying
        `browser_params['profile_archive_dir']`.
    * Save on-demand with the `CommandSequence::dump_profile` command.
* Rendered Page Source
    * Save the top-level frame's rendered source with the
    `CommandSequence::dump_page_source` command.
    * Save the full rendered source (including all nested iframes) with the
    `CommandSequence::recursive_dump_page_source` command.
        * The page source is saved in the following nested json structure:
        ```
        {
            'doc_url': "http://example.com",
            'source': "<html> ... </html>",
            'iframes': {
                'frame_1': {'doc_url': ...,
                            'source': ...,
                            'iframes: { ... }},
                'frame_2': {'doc_url': ...,
                            'source': ...,
                            'iframes: { ... }},
                'frame_3': { ... }
            }
        }
        ```
* Screenshots
    * Selenium 3 can be used to screenshot an individual element. None of the
        built-in commands offer this functionality, but you can use it when
        [writing your own](https://github.com/citp/OpenWPM/wiki/Platform-Demo#adding-a-new-command). See the [Selenium documentation](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html?highlight=element#selenium.webdriver.remote.webelement.WebElement.screenshot).
    * Viewport screenshots (i.e. a screenshot of the portion of the website
        visible in the browser's window) are available with the
        `CommandSequence::save_screenshot` command.
    * Full-page screenshots (i.e. a screenshot of the entire rendered DOM) are
        available with the `CommandSequence::screenshot_full_page` command.
        * This functionality is not yet supported by Selenium/geckodriver,
          though [it is planned](https://github.com/mozilla/geckodriver/issues/570).
          We produce screenshots by using JS to scroll the page and take a
          viewport screenshot at each location. This method will save the parts
          and a stitched version in the `screenshot_path`.
        * Since the screenshots are stitched they have some limitations:
            * On the area of the page present when the command is called will
              be captured. Sites which dynamically expand when scrolled (i.e.,
              infinite scroll) will only go as far as the original height.
            * We only scroll vertically, so pages that are wider than the
              viewport will be clipped.
            * In geckodriver v0.15 doing any scrolling (or having devtools
              open) seems to break element-only screenshots. So using this
              command will cause any future element-only screenshots to be
              misaligned.

Output Format
-------------

#### Local Databases
By default OpenWPM saves all data locally on disk in a variety of formats.
Most of the instrumentation saves to a SQLite database specified
by `manager_params['database_name']` in the main output directory. Response
bodies are saved in a LevelDB database named `content.ldb`, and are keyed by
the hash of the content. In addition, the browser commands that dump page
source and save screenshots save them in the `sources` and `screenshots`
subdirectories of the main output directory. The SQLite schema
specified by: `automation/DataAggregator/schema.sql`. You can specify additional tables
inline by sending a `create_table` message to the data aggregator.

#### Parquet on Amazon S3 **Experimental**
As an option, OpenWPM can save data directly to an Amazon S3 bucket as a
Parquet Dataset. This is currently experimental and hasn't been thoroughly
tested. Screenshots, and page source saving is not currently supported and
will still be stored in local databases and directories. To enable S3
saving specify the following configuration parameters in `manager_params`:
* Output format: `manager_params['output_format'] = 's3'`
* S3 bucket name: `manager_params['s3_bucket'] = 'openwpm-test-crawl'`
* Directory within S3 bucket: `manager_params['s3_directory'] = '2018-09-09_test-crawl-new'`

In order to save to S3 you must have valid access credentials stored in
`~/.aws`. We do not currently allow you to specify an alternate storage
location.

**NOTE:** The schemas should be kept in sync with the exception of
output-specific columns (e.g., `instance_id` in the S3 output). You can compare
the two schemas by running
`diff -y automation/DataAggregator/schema.sql automation/DataAggregator/parquet_schema.py`.

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

* `bot_mitigation`
  * Performs some actions to prevent the platform from being detected as a bot.
  * Note, these aren't comprehensive and automated interaction with the site
    will still appear very bot-like.
* `disable_flash`
  * Flash is disabled by default. Set this to `False` to re-enable. Note that
    flash cookies are shared between browsers.
* `headless`
  * Launch the browser in headless mode (supported as of Firefox 56),
    no GUI will be visible.
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
* `disconnect`
  * Set to `True` to enable Disconnect with all blocking enabled
  * The filter list may be automatically updated. We recommend checking the version of the xpi [located here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions), which may be outdated.
* `ghostery`
  * Set to `True` to enable Ghostery with all blocking enabled
  * The filter list won't be automatically updated. We recommend checking the version of the xpi [located here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions), which may be outdated.
* `https-everywhere`
  * Set to `True` to enable HTTPS Everywhere in the browser.
  * The filter list won't be automatically updated. We recommend checking the version of the xpi [located here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions), which may be outdated.
* `ublock-origin`
  * Set to `True` to enable uBlock Origin in the browser.
  * The filter lists may be automatically updated. We recommend checking the version of the xpi [located here](https://github.com/citp/OpenWPM/tree/master/automation/DeployBrowsers/firefox_extensions), which may be outdated.
* `tracking-protection`
  * **NOT SUPPORTED.** See [#101](https://github.com/citp/OpenWPM/issues/101).
  * Set to `True` to enable Firefox's built-in
    [Tracking Protection](https://developer.mozilla.org/en-US/Firefox/Privacy/Tracking_Protection).

Browser Profile Support
-----------------------

**WARNING: Stateful crawls are currently not supported. Attempts to run
stateful crawls will throw `NotImplementedError`s. The work required to
restore support is tracked in
[this project](https://github.com/mozilla/OpenWPM/projects/2).**

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
    command_sequence.dump_flash_cookies(120)
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

### Types Annotations in Python

We as maintainers have decided it would be helpful to have Python3 type annotations
for the python part of this project to catch errors earlier, get better
code completion and allow bigger changes down the line with more confidence.
As such you should strive to add type annotations to all new code you add to
the project as well as the one you plan to change fundamentally.

### Editing instrumentation

The instrumentation extension is included in `/automation/Extension/firefox/`.
The instrumentation itself (used by the above extension) is included in
`/automation/Extension/webext-instrumentation/`.
Any edits within these directories will require the extension to be re-built to produce
a new `openwpm.xpi` with your updates. You can use `build_extension.sh` to do this.

### Debugging the platform

Manual debugging with OpenWPM can be difficult. By design the platform runs all
browsers in separate processes and swallows all exceptions (with the intent of
continuing the crawl). We recommend using
[manual_test.py](https://github.com/citp/OpenWPM/blob/master/test/manual_test.py).

This utility allows manual debugging of the extension instrumentation with or
without Selenium enabled, as well as makes it easy to launch a Selenium
instance (without any instrumentation)
* `build-extension.sh`
* `python -m test.manual_test` builds the current extension directory
  and launches a Firefox instance with it.
* `python -m test.manual_test --selenium` launches a Firefox Selenium instance
  after automatically rebuilding `openwpm.xpi`. The script then
  drops into an `ipython` shell where the webdriver instance is available
  through variable `driver`.
* `python -m test.manual_test --selenium --no_extension` launches a Firefox Selenium
  instance with no instrumentation. The script then
  drops into an `ipython` shell where the webdriver instance is available
  through variable `driver`.


### Managing requirements

We use [`pip-tools`](https://github.com/jazzband/pip-tools) to pin
requirements. This means that the `requirements.txt` and `requirements-dev.txt`
files should not be edited directly. Instead, place new requirements in
`requirements.in` or `requirements-dev.in`. Requirements necessary to run
OpenWPM should be placed in the former, while those only required to run the
tests (or perform other development tasks) should be placed in the latter.

To update dependencies, run the following two commands **in order**:
* `pip-compile --upgrade requirements.in`
* `pip-compile --upgrade requirements-dev.in`

It's important that these are run in order, as we layer the dev
dependencies on the output of the pinned production dependencies as per
[the official documentation](https://github.com/jazzband/pip-tools#workflow-for-layered-requirements).
This means you may need to manually pin some versions of a dependency in
`requirements.in` so there exists a compatible version for a dependency in
`requirements-dev.in`. Before you run an upgrade, check if the previous pins
that are related to layering in `requirements.in` are still necessary by
removing them and attempting an upgrade without the pins.

### Running tests

OpenWPM's tests are build on `py.test`. To run the tests you will need a few
additional dependencies, which can be installed by running `install-dev.sh`.

Once installed, execute `py.test -vv` in the test directory to run all tests.


### Mac OSX (Limited support for developers)

We've added an installation file to make it easier to run tests and develop on
Mac OSX. To install the dependencies on Mac OSX, run `install-mac-dev.sh`
instead of `install.sh` and `install-dev.sh` in [the official getting started
instructions](https://github.com/mozilla/OpenWPM/wiki/Setting-Up-OpenWPM).

This will install Python packages in a local Python 3 virtualenv,
download the latest Unbranded Firefox Release into the current folder,
move geckodriver next to the Firefox binary and install development dependencies.
For the OpenWPM to be aware of which Firefox installation to run, set the
FIREFOX_BINARY environment variable before running any commands.

Example, running a demo crawl on Mac OSX:

    source venv/bin/activate
    export FIREFOX_BINARY="$(PWD)/Nightly.app/Contents/MacOS/firefox-bin"
    python demo.py

Running the OpenWPM tests on Mac OSX:

    source venv/bin/activate
    export FIREFOX_BINARY="$(PWD)/Nightly.app/Contents/MacOS/firefox-bin"
    python -m pytest -vv

For more detailed setup instructions for Mac, see [Running OpenWPM natively on macOS](https://github.com/mozilla/OpenWPM/wiki/Running-OpenWPM-natively-on-macOS).

We do not run CI tests for Mac, so new issues may arise. We welcome PRs to fix
these issues and add full support and CI testing for Mac.

Troubleshooting
---------------

1. `WebDriverException: Message: The browser appears to have exited before we could connect...`

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

Docker Deployment for OpenWPM
-----------------------------

OpenWPM can be run in a Docker container. This is similar to running OpenWPM in
a virtual machine, only with less overhead.

### Building the Docker Container

__Step 1:__ install Docker on your system. Most Linux distributions have Docker
in their repositories. It can also be installed from
[docker.com](https://www.docker.com/). For Ubuntu you can use:
`sudo apt-get install docker.io`

You can test the installation with: `sudo docker run hello-world`

_Note,_ in order to run Docker without root privileges, add your user to the
`docker` group (`sudo usermod -a -G docker $USER`). You will have to
logout-login for the change to take effect, and possibly also restart the
Docker service.

__Step 2:__ to build the image, run the following command from a terminal
within the root OpenWPM directory:

```
    docker build -f Dockerfile -t openwpm .
```

After a few minutes, the container is ready to use.

### Running Measurements from inside the Container

You can run the demo measurement from inside the container, as follows:

First of all, you need to give the container permissions on your local
X-server. You can do this by running: `xhost +local:docker`

Then you can run the demo script using:

```
    mkdir -p docker-volume && docker run -v $PWD/docker-volume:/root/Desktop \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --shm-size=2g \
    -it openwpm python3 /opt/OpenWPM/demo.py
```

**Note:** the `--shm-size=2g` parameter is required, as it increases the
amount of shared memory available to Firefox. Without this parameter you can
expect Firefox to crash on 20-30% of sites.

This command uses _bind-mounts_ to share scripts and output between the
container and host, as explained below (note the paths in the command assume
it's being run from the root OpenWPM directory):

- `run` starts the `openwpm` container and executes the
    `python /opt/OpenWPM/demo.py` command.

- `-v` binds a directory on the host (`$PWD/docker-volume`) to a
    directory in the container (`/root`). Binding allows the script's
    output to be saved on the host (`./docker-volume/Desktop`), and also allows
    you to pass inputs to the docker container (if necessary). We first create
    the `docker-volume` direction (if it doesn't exist), as docker will
    otherwise create it with root permissions.

- The `-it` option states the command is to be run interactively (use
    `-d` for detached mode).

- The demo scripts runs instances of Firefox that are not headless. As such,
    this command requires a connection to the host display server. If you are
    running headless crawls you can remove the following options:
    `-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix`.

Alternatively, it is possible to run jobs as the user _openwpm_ in the container
too, but this might cause problems with none headless browers. It is therefore
only recommended for headless crawls.

### MacOS GUI applications in Docker

**Requirements**: Install XQuartz by following [these instructions](https://stackoverflow.com/a/47309184).

Given properly installed prerequisites (including a reboot), the helper script
`run-on-osx-via-docker.sh` in the project root folder can be used to facilitate
working with Docker in Mac OSX.

To open a bash session within the environment:

    ./run-on-osx-via-docker.sh /bin/bash

Or, run commands directly:

    ./run-on-osx-via-docker.sh python demo.py
    ./run-on-osx-via-docker.sh python -m test.manual_test
    ./run-on-osx-via-docker.sh python -m pytest
    ./run-on-osx-via-docker.sh python -m pytest -vv -s

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

OpenWPM has been used in over [30 studies](https://webtransparency.cs.princeton.edu/webcensus/index.html#Users).

License
-------

OpenWPM is licensed under GNU GPLv3. Additional code has been included from
[FourthParty](https://github.com/fourthparty/fourthparty) and
[Privacy Badger](https://github.com/EFForg/privacybadgerfirefox), both of which
are licensed GPLv3+.
