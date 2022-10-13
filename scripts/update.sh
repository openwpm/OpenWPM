#!/bin/bash

set -e

pushd scripts
./repin.sh
popd

# Make conda available to shell script
eval "$(conda shell.bash hook)"

conda activate openwpm

npm update --dev

pushd Extension
npm update --dev
popd
popd