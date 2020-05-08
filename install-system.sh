#!/bin/bash
set -e

if [[ $# -gt 0 ]]; then
    echo "Usage: install.sh" >&2
    exit 1
fi

sudo apt-get update

sudo apt-get install -y firefox htop git libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential libboost-python-dev libleveldb-dev libjpeg-dev curl wget git bash vim xvfb

# For some versions of ubuntu, the package libleveldb1v5 isn't available. Use libleveldb1 instead.
sudo apt-get install -y libleveldb1v5 || sudo apt-get install -y libleveldb1

# Use the Unbranded build that corresponds to a specific Firefox version 
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.
TAG=6200ca9b300670ec069cdbf6e4f05e6a0bca46f1 # FIREFOX_75_0_RELEASE
UNBRANDED_RELEASE_LINUX_BUILD="https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/gecko.v2.mozilla-release.revision.$TAG.firefox.linux64-add-on-devel/artifacts/public/build/target.tar.bz2"
wget "$UNBRANDED_RELEASE_LINUX_BUILD"
tar jxf target.tar.bz2
rm -rf firefox-bin
mv firefox firefox-bin
rm target.tar.bz2

# Selenium 3.3+ requires a 'geckodriver' helper executable, which is not yet
# packaged.
GECKODRIVER_VERSION=0.26.0
case $(uname -m) in
    (x86_64)
        GECKODRIVER_ARCH=linux64
        ;;
    (*)
        echo Platform $(uname -m) not known to be supported by geckodriver >&2
        exit 1
        ;;
esac
wget https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
tar zxf geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
rm geckodriver-v${GECKODRIVER_VERSION}-${GECKODRIVER_ARCH}.tar.gz
mv geckodriver firefox-bin
