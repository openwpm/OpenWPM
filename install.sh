#!/bin/bash
set -e

if [[ $# -gt 1 ]]; then
    echo "Usage: install.sh [--flash | --no-flash]" >&2
    exit 1
fi

if [[ $# -gt 0 ]]; then
    case "$1" in
        "--flash")
            flash=true
            ;;
        "--no-flash")
            flash=false
            ;;
        *)
            echo "Usage: install.sh [--flash | --no-flash]" >&2
            exit 1
            ;;
    esac
else
    echo "Would you like to install Adobe Flash Player? (Only required for crawls with Flash) [y,N]"
    read -s -n 1 response
    if [[ $response = "" ]] || [ $response == 'n' ] || [ $response == 'N' ]; then
        flash=false
        echo Not installing Adobe Flash Plugin
    elif [ $response == 'y' ] || [ $response == 'Y' ]; then
        flash=true
        echo Installing Adobe Flash Plugin
    else
        echo Unrecognized response, exiting
        exit 1
    fi
fi

if [ "$flash" = true ]; then
    sudo sh -c 'echo "deb http://archive.canonical.com/ubuntu/ trusty partner" >> /etc/apt/sources.list.d/canonical_partner.list'
fi
sudo apt-get update

sudo apt-get install -y firefox htop git python-dev libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb libboost-python-dev libleveldb-dev libjpeg-dev curl wget

# For some versions of ubuntu, the package libleveldb1v5 isn't available. Use libleveldb1 instead.
sudo apt-get install -y libleveldb1v5 || sudo apt-get install -y libleveldb1

if [ "$flash" = true ]; then
    sudo apt-get install -y adobe-flashplugin
fi

# Check if we're running on continuous integration
# Python requirements are already installed by .travis.yml on Travis
if [ "$TRAVIS" != "true" ]; then
      wget https://bootstrap.pypa.io/get-pip.py
      sudo -H python get-pip.py
      rm get-pip.py
      sudo -H pip install -r pipenv.txt
      pipenv install -r requirements.txt --skip-lock
fi

# Grab the latest version of Firefox ESR.
# For security reasons it is very important to keep up with patch releases
# of the ESR, but a major version bump needs to be tested carefully.
# Older ESRs are not supported by geckodriver.
firefox_version="$(curl 'https://ftp.mozilla.org/pub/firefox/releases/' |
grep '/pub/firefox/releases/52.' |
tail -n 1 | sed -e 's/.*releases\///g' | cut -d '/' -f1)"

wget https://ftp.mozilla.org/pub/firefox/releases/${firefox_version}/linux-$(uname -m)/en-US/firefox-${firefox_version}.tar.bz2
tar jxf firefox-${firefox_version}.tar.bz2
rm -rf firefox-bin
mv firefox firefox-bin
rm firefox-${firefox_version}.tar.bz2

# Selenium 3.3+ requires a 'geckodriver' helper executable, which is not yet
# packaged. `geckodriver` 0.16.0+ is not compatible with Firefox 52. See:
# https://github.com/mozilla/geckodriver/issues/743
GECKODRIVER_VERSION=0.15.0
case $(uname -m) in
    (x86_64)
        GECKODRIVER_ARCH=linux64
        ;;
    (*)
        echo Platform $(uname -m) not known to be supported by geckodriver >&2
        exit 1
        ;;
esac
wget https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
tar zxf geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
rm geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
mv geckodriver firefox-bin
