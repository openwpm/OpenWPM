#!/bin/bash
set -e

if [[ $# -gt 1 ]]; then
    echo "Usage: install-flash-ubuntu.sh [--flash | --no-flash]" >&2
    exit 1
fi

if [[ $# -gt 0 ]]; then
    case "$1" in
        "--flash")
            flash=true
            ;;
        "--no-flash")
            flash=false
            ;;
        *)
            echo "Usage: install.sh [--flash | --no-flash]" >&2
            exit 1
            ;;
    esac
else
    echo "Would you like to install Adobe Flash Player? (Only required for crawls with Flash) [y,N]"
    read -s -n 1 response
    if [[ $response = "" ]] || [ $response == 'n' ] || [ $response == 'N' ]; then
        flash=false
        echo Not installing Adobe Flash Plugin
    elif [ $response == 'y' ] || [ $response == 'Y' ]; then
        flash=true
        echo Installing Adobe Flash Plugin
    else
        echo Unrecognized response, exiting
        exit 1
    fi
fi
if [ "$flash" = true ]; then
    sudo add-apt-repository "deb http://archive.canonical.com/ $(lsb_release -sc) partner"
fi
sudo apt-get update
if [ "$flash" = true ]; then
    sudo apt-get install -y adobe-flashplugin
fi
dd
