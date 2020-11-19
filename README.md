
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
* [Troubleshooting](#troubleshooting)
* [Advice for Measurement Researchers](#advice-for-measurement-researchers)
* [Developer instructions](#developer-instructions)
* [Instrumentation and Configuration](#instrumentation-and-configuration)
* [Persistence Types](#persistence-types)
    * [Local Databases](#local-databases)
    * [Parquet on Amazon S3](#parquet-on-amazon-s3)
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
`openwpm/default_manager_params.json` and
`openwpm/default_browser_params.json`, with the exception of the changes
specified in `demo.py`.

More information on the instrumentation and configuration parameters is given
below.


The docs provide a more [in-depth tutorial](docs/Using_OpenWPM.md),
and a description of the [methods of data collection](docs/Configuration.md#Instruments)
available.

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
   `openwpm/DeployBrowsers/configure_firefox.py`.

3. Make sure you're conda environment is activated (`conda activate openwpm`). You can see
   you environments and the activate one by running `conda env list` the active environment
   will have a `*` by it.

4. `make` / `gcc` may need to be installed in order to build the web extension.
   On Ubuntu, this is achieved with `apt-get install make`. On OSX the necessary
   packages are part of xcode: `xcode-select --install`.
5. On a very sparse operating system additional dependencies may need to be
   installed. See the [Dockerfile](Dockerfile) for more inspiration, or open
   an issue if you are still having problems.
6. If you see errors related to incompatible or non-existing python packages,
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

If you want to contribute to OpenWPM have a look at our [CONTRIBUTING.md](./CONTRIBUTING.md)

Instrumentation and Configuration
-------------------------------
OpenWPM provides a breadth of configuration options which can be found
in [Configuration.md](docs/Configuration.md)
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
specified by: `openwpm/DataAggregator/schema.sql`. You can specify additional tables
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
`diff -y openwpm/DataAggregator/schema.sql openwpm/DataAggregator/parquet_schema.py`.

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
    mkdir -p docker-volume && docker run -v $PWD/docker-volume:/opt/Desktop \
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

OpenWPM has been used in over [75 studies](https://webtap.princeton.edu/software/).

License
-------

OpenWPM is licensed under GNU GPLv3. Additional code has been included from
[FourthParty](https://github.com/fourthparty/fourthparty) and
[Privacy Badger](https://github.com/EFForg/privacybadgerfirefox), both of which
are licensed GPLv3+.
