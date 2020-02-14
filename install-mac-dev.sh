#!/bin/bash
set -e

# Note: This install script assumes that node and python is already setup
# and is meant for setting up local development rather than CI environments

if [[ $# -gt 0 ]]; then
    echo "Usage: install-mac.sh" >&2
    exit 1
fi

# Create and activate a local Python 3 venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install all requirements except plyvel
cat requirements.txt | grep -v plyvel > requirements.mac.txt
CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install -r requirements.mac.txt
rm requirements.mac.txt

# A recent version of leveldb is required
brew install leveldb || brew upgrade leveldb

# Make sure we build plyvel properly to work with the installed leveldb on recent OSX versions
CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++ -std=c++11' pip install --force-reinstall --ignore-installed --no-binary :all: plyvel

# Make npm available (used by build-extension.sh)
brew install node || true

# Use the Unbranded build that corresponds to a specific Firefox version 
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.
brew install wget || true

TAG=25e0edbb0a613c3bf794c93ba3aa0985d29d5ef4
UNBRANDED_RELEASE_MAC_BUILD="https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/gecko.v2.mozilla-release.revision.$TAG.firefox.macosx64-add-on-devel/artifacts/public/build/target.dmg"
wget "$UNBRANDED_RELEASE_MAC_BUILD"
# Install Firefox Nightly
rm -rf Nightly.app || true
hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp target.dmg
cp -r /Volumes/firefox-tmp/Nightly.app .
hdiutil detach /Volumes/firefox-tmp
rm target.dmg

# Selenium 3.3+ requires a 'geckodriver' helper executable, which is not yet
# packaged.
GECKODRIVER_VERSION=0.26.0
GECKODRIVER_ARCH=macos

wget https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
tar zxf geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
rm geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
mv geckodriver Nightly.app/Contents/MacOS/

# Download and build client extension
./build-extension.sh

# Install requirements related to OpenWPM development
pip install -U -r requirements-dev.txt
