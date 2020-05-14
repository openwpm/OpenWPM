#!/bin/bash

# This script builds and installs the
# webextension instrumentation.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"
conda activate openwpm

echo '**********************xxxxxxxxxxxxxxx'
node --version

pushd automation/Extension/firefox
npm install
npm run build
cp dist/*.zip ./openwpm.xpi
popd

echo "Success: automation/Extension/firefox/openwpm.xpi has been built"
