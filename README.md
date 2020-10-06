
OpenWPM
[![Build Status](https://travis-ci.org/mozilla/OpenWPM.svg?branch=master)](https://travis-ci.org/mozilla/OpenWPM)
[![OpenWPM Matrix Channel](https://img.shields.io/matrix/OpenWPM:mozilla.org?label=Join%20us%20on%20matrix&server_fqdn=mozilla.modular.im)](https://matrix.to/#/#OpenWPM:mozilla.org?via=mozilla.org) <!-- omit in toc -->
=======

OpenWPM is a web privacy measurement framework which makes it easy to
collect data for privacy studies on a scale of thousands to millions
of websites. OpenWPM is built on top of Firefox, with automation provided
by Selenium. It includes several hooks for data collection. Check out
the instrumentation section below for more details.

Table of Contents <!-- omit in toc -->
------------------
* [Installation](#installation)
  * [Pre-requisites](#pre-requisites)
  * [Install](#install)
  * [Mac OSX](#mac-osx)
* [Quick Start](#quick-start)
* [Advice for Measurement Researchers](#advice-for-measurement-researchers)
* [Developer instructions](#developer-instructions)
* [Instrumentation and Data Access](#instrumentation-and-data-access)
* [Persistence Types](#persistence-types)
    * [Local Databases](#local-databases)
    * [Parquet on Amazon S3](#parquet-on-amazon-s3)
* [Browser and Platform Configuration](#browser-and-platform-configuration)
  * [Platform Configuration Options](#platform-configuration-options)
  * [Browser Configuration Options](#browser-configuration-options)
* [Browser Profile Support](#browser-profile-support)
  * [Stateful vs Stateless crawls](#stateful-vs-stateless-crawls)
  * [Loading and saving a browser profile](#loading-and-saving-a-browser-profile)
    * [Save a profile](#save-a-profile)
    * [Load a profile](#load-a-profile)
* [Troubleshooting](#troubleshooting)
* [Docker Deployment for OpenWPM](#docker-deployment-for-openwpm)
  * [Building the Docker Container](#building-the-docker-container)
  * [Running Measurements from inside the Container](#running-measurements-from-inside-the-container)
  * [MacOS GUI applications in Docker](#macos-gui-applications-in-docker)
* [Citation](#citation)
* [License](#license)


Installation
------------

OpenWPM is tested on Ubuntu 18.04 via TravisCI and is commonly used via the docker container
that this repo builds, which is also based on Ubuntu. Although we don't officially support
other platforms, conda is a cross platform utility and the install script can be expected
to work on OSX and other linux distributions.

OpenWPM does not support windows: https://github.com/mozilla/OpenWPM/issues/503


### Pre-requisites

The main pre-requisite for OpenWPM is conda, a cross-platform package management tool.

Conda is open-source, and can be installed from https://docs.conda.io/en/latest/miniconda.html.

### Install

An installation script, `install.sh` is included to: install the conda environment,
install unbranded firefox, and build the instrumentation extension.

All installation is confined to your conda environment and should not affect your machine.
The installation script will, however, override any existing conda environment named openwpm.

To run the install script, run

    $ ./install.sh

After running the install script, activate your conda environment by running:

    $ conda activate openwpm

### Mac OSX

You may need to install `make` / `gcc` in order to build the extension.
The necessary packages are part of xcode: `xcode-select --install`

We do not run CI tests for Mac, so new issues may arise. We welcome PRs to fix
these issues and add full CI testing for Mac.

Running Firefox with xvfb on OSX is untested and will require the user to install
an X11 server. We suggest [XQuartz](https://www.xquartz.org/). This setup has not
been tested, we welcome feedback as to whether this is working.



Quick Start
-----------

Once installed, it is very easy to run a quick test of OpenWPM. Check out
`demo.py` for an example. This will use the default setting specified in
`automation/default_manager_params.json` and
`automation/default_browser_params.json`, with the exception of the changes
specified in `demo.py`.

More information on the instrumentation and configuration parameters is given
below.


The docs provide a more [in-depth tutorial](docs/Using_OpenWPM.md),
and a description of the [methods of data collection](docs/Instruments.md)
available.


Advice for Measurement Researchers
----------------------------------

OpenWPM is [often used](https://webtap.princeton.edu/software/) for web
measurement research. We recommend the following for researchers using the tool:

**Use a versioned [release](https://github.com/mozilla/OpenWPM/releases).** We
aim to follow Firefox's release cadence, which is roughly once every four
weeks. If we happen to fall behind on checking in new releases, please file an
issue. Versions more than a few months out of date will use unsupported
versions of Firefox, which are likely to have known security
vulnerabilities. Versions less than v0.10.0 are from a previous architecture
and should not be used.

**Include the OpenWPM version number in your publication.** As of v0.10.0
OpenWPM pins all python, npm, and system dependencies. Including this
information alongside your work will allow other researchers to contextualize
the results, and can be helpful if future versions of OpenWPM have
instrumentation bugs that impact results.

Developer instructions
----------------------

If you want to contribute to OpenWPM have a look at our [CONTRIBUTING.md](docs/CONTRIBUTING.md)

Instrumentation and Data Access
-------------------------------
OpenWPM provides several instrumentation modules which can be enabled
independently of each other for each crawl.
A list of all instruments, their functions and their output formats can be
found [here](docs/Instruments.md)
More detail on the output is available [below](#persistence-types).

Persistence Types
------------

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

#### Parquet on Amazon S3
As an option, OpenWPM can save data directly to an Amazon S3 bucket as a
Parquet Dataset. This is currently experimental and hasn't been thoroughly
tested. Screenshots, and page source saving is not currently supported and
will still be stored in local databases and directories. To enable S3
saving specify the following configuration parameters in `manager_params`:
* Persistence Type: `manager_params['output_format'] = 's3'`
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
* `display_mode`:
  * `native`:
    * Launch the browser normally - GUI will be visible
  * `headless`:
    * Launch the browser in headless mode (supported as of Firefox 56),
        no GUI will be visible.
    * Use this when running browsers on a remote machine or to run crawls in the
        background on a local machine.
  * `xvfb`:
    * Launch the browser using the X virtual frame buffer. In this mode, Firefox
      is not running in it's own headless mode, but no GUI will be displayed.
    * This mode requires `Xvfb` to be on your path. On Ubuntu that is achieved by running
      `sudo apt-get install xvfb`. For other platforms check [www.X.org](http://www.X.org).
  * `headless` mode and `xvfb` are not equivalent. `xvfb` is a full browser, but you get
    "headless" browsing because you do not need to be in a full X environment e.g. on a
    server. `headless` mode is supported on all platforms and is implemented by the browser
    but has some differences. For example webGL is not supported in headless mode.
    https://github.com/mozilla/OpenWPM/issues/448 discusses additional factors to consider
    when picking a `display_mode`.
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

#### Load a profile

To load a profile, specify the `seed_tar` browser parameter in the browser
configuration dictionary. This should point to the location of the
`profile.tar` or (`profile.tar.gz` if compressed) file produced by OpenWPM
or by manually tarring a firefox profile directory.
The profile will be automatically extracted and loaded into the browser
instance for which the configuration parameter was set.

The profile specified by `seed_tar` will be loaded anytime the browser is
deliberately reset (i.e., using the `reset=True` CommandSequence argument),
but will not be used during crash recovery. Specifically:
* For stateful crawls the initial load of Firefox will use the
profile specified by `seed_tar`. If OpenWPM determines that Firefox needs to
restart for some reason during the crawl, it will use the profile from
the most recent page visit (pre-crash) rather than the `seed_tar` profile.
Note that stateful crawl are currently [unsupported](https://github.com/mozilla/OpenWPM/projects/2)).
* For stateless crawls, the initial `seed_tar` will be loaded during each
new page visit. Note that this means the profile will very likely be
_incomplete_, as cookies or storage may have been set or changed during the
page load that are **not** reflected back into the seed profile.


Troubleshooting
---------------

1. `WebDriverException: Message: The browser appears to have exited before we could connect...`

  This error indicates that Firefox exited during startup (or was prevented from
  starting). There are many possible causes of this error:

  * If you are seeing this error for all browser spawn attempts check that:
    * Both selenium and Firefox are the appropriate versions. Run the following
      commands and check that the versions output match the required versions in
      `install.sh` and `environment.yaml`. If not, re-run the install script.
      ```sh
      cd firefox-bin/
      firefox --version
      ```

      and

      ```sh
        conda list selenium
      ```
    * If you are running in a headless environment (e.g. a remote server), ensure
      that all browsers have the `headless` browser parameter set to `True` before
      launching.
  * If you are seeing this error randomly during crawls it can be caused by
    an overtaxed system, either memory or CPU usage. Try lowering the number of
    concurrent browsers.

2. In older versions of firefox (pre 74) the setting to enable extensions was called
   `extensions.legacy.enabled`. If you need to work with earlier firefox, update the
   setting name `extensions.experiments.enabled` in
   `automation/DeployBrowsers/configure_firefox.py`.

3. Make sure you're conda environment is activated (`conda activate openwpm`). You can see
   you environments and the activate one by running `conda env list` the active environment
   will have a `*` by it.

1. `make` / `gcc` may need to be installed in order to build the web extension.
   On Ubuntu, this is achieved with `apt-get install make`. On OSX the necessary
   packages are part of xcode: `xcode-select --install`.
2. On a very sparse operating system additional dependencies may need to be
   installed. See the [Dockerfile](Dockerfile) for more inspiration, or open
   an issue if you are still having problems.
3. If you see errors related to incompatible or non-existing python packages,
   try re-running the file with the environment variable
   `PYTHONNOUSERSITE` set. E.g., `PYTHONNOUSERSITE=True python demo.py`.
   If that fixes your issues, you are experiencing
   [issue 689](https://github.com/mozilla/OpenWPM/issues/689), which can be
   fixed by clearing your
   python [user site packages directory](https://www.python.org/dev/peps/pep-0370/),
   by prepending `PYTHONNOUSERSITE=True` to a specific command, or by setting
   the environment variable for the session (e.g., `export PYTHONNOUSERSITE=True`
   in bash). Please also add a comment to that issue to let us know you ran
   into this problem.



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
