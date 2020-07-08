#!/bin/bash

# This script builds and installs the
# webextension instrumentation.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"
conda activate openwpm

pushd automation/Extension/firefox
npm install
pushd ../webext-instrumentation
npm install
popd
npm run build
popd

echo "Success: automation/Extension/firefox/openwpm.xpi has been built"
