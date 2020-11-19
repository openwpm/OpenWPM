#!/bin/bash

# This script builds and installs the
# webextension instrumentation.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"
conda activate openwpm

pushd openwpm/Extension/firefox
npm install --legacy-peer-deps
pushd ../webext-instrumentation
npm install
popd
npm run build
popd

echo "Success: openwpm/Extension/firefox/openwpm.xpi has been built"
