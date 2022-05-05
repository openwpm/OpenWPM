#!/bin/bash
set -e
# Use the Unbranded build that corresponds to a specific Firefox version
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.

# Note this script is **destructive** and will
# remove the existing Firefox in the OpenWPM directory

TAG='1c7f7adc90e2b4c8d64548938bb1499033c5be8f' # FIREFOX_100_0_RELEASE

case "$(uname -s)" in
   Darwin)
     echo 'Installing for Mac OSX'
     OS='macosx'
     TARGET_SUFFIX='.dmg'
     ;;
   Linux)
     echo 'Installing for Linux'
     OS='linux'
     TARGET_SUFFIX='.tar.bz2'
     ;;
   *)
     echo 'Your OS is not supported. Aborting'
     exit 1
     ;;
esac

UNBRANDED_RELEASE_BUILD="https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/gecko.v2.mozilla-release.revision.${TAG}.firefox.${OS}64-add-on-devel/artifacts/public/build/target${TARGET_SUFFIX}"
wget -q "$UNBRANDED_RELEASE_BUILD"

case "$(uname -s)" in
   Darwin)
     rm -rf Nightly.app || true
     hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp target.dmg
     cp -r /Volumes/firefox-tmp/Nightly.app .
     hdiutil detach /Volumes/firefox-tmp
     rm target.dmg
     ;;
   Linux)
     tar jxf target.tar.bz2
     rm -rf firefox-bin
     mv firefox firefox-bin
     rm target.tar.bz2
     ;;
esac

echo 'Firefox succesfully installed'
