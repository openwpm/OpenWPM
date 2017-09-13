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

# Install specific version of Firefox known to work well with the selenium version above
if [ $(uname -m) == 'x86_64' ]; then
  echo Downloading 64-bit Firefox
  wget https://ftp.mozilla.org/pub/firefox/releases/45.9.0esr/linux-x86_64/en-US/firefox-45.9.0esr.tar.bz2
else
  echo Downloading 32-bit Firefox
  wget https://ftp.mozilla.org/pub/firefox/releases/45.9.0esr/linux-i686/en-US/firefox-45.9.0esr.tar.bz2
fi
tar jxf firefox*.tar.bz2
rm -rf firefox-bin
mv firefox firefox-bin
rm firefox*.tar.bz2
