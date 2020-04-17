#!/bin/bash
set -e

./install-system.sh

./install-pip-and-packages.sh

./install-node.sh

# Download and build client extension
./build-extension.sh
