#!/bin/bash
set -e

for arg in "$@"
do
    if [ "$arg" == "--dev" ] || [ "$arg" == "-d" ]
    then
        echo "Installing dev dependencies..."
        ./scripts/install-dev.sh 
    fi
done

./scripts/install-system.sh "$@"

./scripts/install-pip-and-packages.sh

./scripts/install-node.sh

# Download and build client extension
./scripts/build-extension.sh
