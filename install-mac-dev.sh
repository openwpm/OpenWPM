#!/bin/bash
set -e

# Note: This install script assumes that node and python is already setup
# and is meant for setting up local development rather than CI environments

if [[ $# -gt 0 ]]; then
    echo "Usage: install-mac.sh" >&2
    exit 1
fi

brew install leveldb || brew upgrade leveldb

pip install -U -r requirements.txt

# Make npm packages available
brew install node || brew upgrade node

wget https://index.taskcluster.net/v1/task/gecko.v2.mozilla-release.latest.firefox.macosx64-add-on-devel/artifacts/public/build/target.dmg

rm -rf Nightly.app
hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp target.dmg
cp -r /Volumes/firefox-tmp/Nightly.app .
hdiutil detach /Volumes/firefox-tmp
rm target.dmg


# Selenium 3.3+ requires a 'geckodriver' helper executable, which is not yet
# packaged.
GECKODRIVER_VERSION=0.23.0
GECKODRIVER_ARCH=macos

wget https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
tar zxf geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
rm geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
mv geckodriver Nightly.app/Contents/MacOS/

# Download and build client extension
./build-extension.sh

pip install -U -r requirements-dev.txt
