#!/bin/bash

# This script builds and installs the
# webextension instrumentation.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"
conda activate openwpm

pushd Extension
npm ci
popd

echo "Success: Extension/openwpm.xpi has been built"
