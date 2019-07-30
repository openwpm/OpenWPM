#!/bin/bash
set -e

# THIS SCRIPT ASSUMES YOUR CONDA ENVIRONMENT IS ACTIVE

# rm existing Nightly.app
rm -rf Nightly.app || true

# get new target
wget https://queue.taskcluster.net/v1/task/EPaShNEQTYaBrJYpULyxwg/runs/0/artifacts/public/build/target.dmg

# mount and copy to Nightly .
hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp target.dmg
cp -r /Volumes/firefox-tmp/Nightly.app .
hdiutil detach /Volumes/firefox-tmp

# clean up
rm target.dmg
