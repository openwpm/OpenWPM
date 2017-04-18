#!/bin/bash
set -e

echo "Would you like to install Adobe Flash Player? (Only required for crawls with Flash) [y,N]"
read -s -n 1 response
if [[ $response = "" ]] || [ $response == 'n' ] || [ $response == 'N' ]; then
    flash=false
    echo Not installing Adobe Flash Plugin
elif [ $response == 'y' ] || [ $response == 'Y' ]; then
    flash=true
    echo Installing Adobe Flash Plugin
    sudo sh -c 'echo "deb http://archive.canonical.com/ubuntu/ trusty partner" >> /etc/apt/sources.list.d/canonical_partner.list'
else
    echo Unrecognized response, exiting >&2
    exit 1
fi

sudo apt-get update

sudo apt-get install -y firefox htop git python-dev libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb libboost-python-dev libleveldb-dev libjpeg-dev

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
	sudo pip install -U -r requirements.txt
fi

# This is the latest version of Firefox 52ESR as of March 10, 2017.
# For security reasons it is very important to keep up with patch releases
# of the ESR, but a major version bump needs to be tested carefully.
# Older ESRs are not supported by geckodriver.
FIREFOX_VERSION=52.0esr

wget https://ftp.mozilla.org/pub/firefox/releases/${FIREFOX_VERSION}/linux-$(uname -m)/en-US/firefox-${FIREFOX_VERSION}.tar.bz2
tar jxf firefox-${FIREFOX_VERSION}.tar.bz2
rm -rf firefox-bin
mv firefox firefox-bin
rm firefox-${FIREFOX_VERSION}.tar.bz2

# Selenium 3.3 requires a 'geckodriver' helper executable, which is not
# yet packaged.
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
