#!/bin/bash
set -e


if which node > /dev/null
    then
        echo "Node is installed, skipping..."
        exit 0
    else
        # Install node
        curl -sL https://deb.nodesource.com/setup_10.x | sudo bash -
        sudo apt install -y nodejs
    fi