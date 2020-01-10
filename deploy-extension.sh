#!/bin/bash
set -e

cd automation/Extension/firefox
web-ext build
cd -
cp automation/Extension/firefox/dist/openwpm-*.zip firefox-profile/extensions/openwpm@mozilla.org.xpi
if [ -z "$1" ]; then
    firefox-bin/firefox-bin -profile firefox-profile;
else
    $1 -profile firefox-profile;
fi