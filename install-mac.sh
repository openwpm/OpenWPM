#!/bin/bash
set -e

# Note: This install script assumes that node and python is already setup
# and is meant for setting up local development rather than CI environments

if [[ $# -gt 0 ]]; then
    echo "Usage: install-mac.sh" >&2
    exit 1
fi

brew install leveldb

pip install -U -r requirements.txt

# Make npm packages available
brew install node || brew upgrade node

# Grab the latest version of Firefox ESR.
# For security reasons it is very important to keep up with patch releases
# of the ESR, but a major version bump needs to be tested carefully.
# Older ESRs are not supported by geckodriver.
firefox_version="$(curl 'https://ftp.mozilla.org/pub/firefox/releases/' |
grep '/pub/firefox/releases/52.' |
tail -n 1 | sed -e 's/.*releases\///g' | cut -d '/' -f1)"

wget "https://ftp.mozilla.org/pub/firefox/releases/${firefox_version}/mac/en-US/Firefox ${firefox_version}.dmg" -O firefox.dmg

#npm install get-firefox
#npx get-firefox -b esr -p mac -t firefox.dmg

rm -rf Firefox.app
hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp firefox.dmg
cp -r /Volumes/firefox-tmp/Firefox.app .
hdiutil detach /Volumes/firefox-tmp
rm firefox.dmg

# Selenium 3.3+ requires a 'geckodriver' helper executable, which is not yet
# packaged. `geckodriver` 0.16.0+ is not compatible with Firefox 52. See:
# https://github.com/mozilla/geckodriver/issues/743
# npm geckodriver 1.5.x = geckodriver 0.15.0
npm install geckodriver@1.5.0
cp node_modules/geckodriver/geckodriver Firefox.app/Contents/MacOS/

# Dependencies for OpenWPM development -- NOT needed to run the platform.
# * Required for compiling Firefox extension
npm install jpm -g

pip install -U -r requirements-dev.txt
