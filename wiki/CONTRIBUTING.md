# Contributing <!-- omit in toc -->


- [Setting up a dev enviroment](#setting-up-a-dev-enviroment)
- [General Hints and Guidelines](#general-hints-and-guidelines)
  - [Avoid failing tests for PRs caused by formatting/linting issues](#avoid-failing-tests-for-prs-caused-by-formattinglinting-issues)
  - [Types Annotations in Python](#types-annotations-in-python)
  - [Editing instrumentation](#editing-instrumentation)
  - [Debugging the platform](#debugging-the-platform)
  - [Managing requirements](#managing-requirements)
  - [Running tests](#running-tests)
  - [Mac OSX](#mac-osx)
  - [Updating schema docs](#updating-schema-docs)

## Setting up a dev enviroment
Dev dependencies are installed by using the main `environment.yaml` (which
is used by `./install.sh` script).

You can install pre-commit hooks install the hooks by running `pre-commit install` to
lint all the changes before you make a commit.

## General Hints and Guidelines

### Avoid failing tests for PRs caused by formatting/linting issues

If you have `pre-commit` running you should pass all linting in the CI as the lints run before every commit.
If you have chosen not to use pre-commit we recommend you run
a combination of `isort` and `autopep8` to fix errors automatically in-place before you submit your PR:

* `python -m isort -rc --skip venv .`
* `python -m autopep8 -r --in-place --exclude venv .`

Not all errors will be fixed automatically, and sometimes the above commands will change files that are not relevant to your PR. Revert those changes and only include (automatic and manual) changes that are related to the code you are modifying by your PR.


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
a new `openwpm.xpi` with your updates. You can use `./scripts/build-extension.sh` to do this,
or you can run `npm run build` from `automation/Extension/firefox/`.

### Debugging the platform

Manual debugging with OpenWPM can be difficult. By design the platform runs all
browsers in separate processes and swallows all exceptions (with the intent of
continuing the crawl). We recommend using
[manual_test.py](../test/manual_test.py).

This utility allows manual debugging of the extension instrumentation with or
without Selenium enabled, as well as makes it easy to launch a Selenium
instance (without any instrumentation)
* `./scripts/build-extension.sh`
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

We use a script to pin dependencies `scripts/repin.sh`.

This means that `environment.yaml` should not be edited directly.

Instead, place new requirements in `scripts/environment-unpinned.yaml` or `scripts/environment-unpinned-dev.yaml`
and then run repin:

    $ cd scripts
    $ ./repin.sh

To update the version of firefox, the TAG variable must be updated in the `./scripts/install-firefox.sh`
script. This script contains further information about finding the right TAG.

### Running tests

OpenWPM's tests are build on [pytest](https://docs.pytest.org/en/latest/). Execute `py.test -vv`
in the test directory to run all tests:

    $ conda activate openwpm
    $ cd test
    $ py.test -vv

See the [pytest docs](https://docs.pytest.org/en/latest/) for more information on selecting
specific tests and various pytest options.

### Mac OSX

You may need to install `make` / `gcc` in order to build the extension.
The necessary packages are part of xcode: `xcode-select --install`

We do not run CI tests for Mac, so new issues may arise. We welcome PRs to fix
these issues and add full CI testing for Mac.

Running Firefox with xvfb on OSX is untested and will require the user to install
an X11 server. We suggest [XQuartz](https://www.xquartz.org/). This setup has not
been tested, we welcome feedback as to whether this is working.

### Updating schema docs

In the rare instance that you need to create schema docs
(after updating or adding files to `schemas` folder), run `npm install`
from OpenWPM top level. Then run `npm run render_schema_docs`. This will update the
`docs/schemas` folder. You may want to clean out the `docs/schemas` folder before doing this
incase files have been renamed.