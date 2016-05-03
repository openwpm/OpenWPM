#!/bin/bash
set -e

# Dependencies for OpenWPM development -- NOT needed to run the platform.
# * Required for compiling Firefox extension
sudo apt-get install npm

# Fix naming issue
sudo ln -s /usr/bin/nodejs /usr/bin/node

sudo npm install jpm -g
