#!/bin/bash
set -e

# Dependencies for OpenWPM development -- NOT needed to run the platform.
sudo apt-get install -y libsasl2-dev
pip3 install -U -r requirements-dev.txt
