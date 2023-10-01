#!/bin/bash

# This script builds and installs the
# webextension instrumentation.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"
conda activate openwpm

pushd /Users/ayeshaislam/OpenWPM/Extension
npm ci --force
popd

echo "Success: Extension/openwpm.xpi has been built"
