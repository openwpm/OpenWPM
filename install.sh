#!/bin/bash
set -e

for arg in "$@"
do
    if [ "$arg" == "--dev" ] || [ "$arg" == "-d" ]
    then
       
    fi
done

./scripts/install-system.sh "$@"

./scripts/install-pip-and-packages.sh

./scripts/install-node.sh

# Download and build client extension
./scripts/build-extension.sh
