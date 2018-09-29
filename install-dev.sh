#!/bin/bash
set -e

# Dependencies for OpenWPM development -- NOT needed to run the platform.
# * Required for compiling Firefox extension
sudo apt-get -y install npm

# Fix naming issue (exists in 14.04 and 16.04)
if [ ! -f /usr/bin/node ]; then
    sudo ln -s /usr/bin/nodejs /usr/bin/node
fi

sudo npm install jpm -g

pip install --user -U -r requirements-dev.txt
