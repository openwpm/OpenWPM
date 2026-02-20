#!/usr/bin/env bash
set -e
# Use the Unbranded build that corresponds to a specific Firefox version
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.

# Note this script is **destructive** and will
# remove the existing Firefox in the OpenWPM directory

TAG='fc43c97c72749b9e222d68e0d37e7c696ae933e2' # FIREFOX_147_0_4_RELEASE

case "$(uname -s)" in
Darwin)
  echo 'Installing for Mac OSX'
  OS='macosx'
  TARGET_SUFFIX='.dmg'
  ;;
Linux)
  echo 'Installing for Linux'
  OS='linux'
  TARGET_SUFFIX='.tar.xz'
  ;;
*)
  echo 'Your OS is not supported. Aborting'
  exit 1
  ;;
esac

UNBRANDED_RELEASE_BUILD="https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/gecko.v2.mozilla-release.revision.${TAG}.firefox.${OS}64-add-on-devel/artifacts/public/build/target${TARGET_SUFFIX}"
echo "Downloading Firefox from: $UNBRANDED_RELEASE_BUILD"
if ! wget -q --show-progress -O "target${TARGET_SUFFIX}" "$UNBRANDED_RELEASE_BUILD"; then
  echo "Error: Failed to download Firefox. Check your network connection."
  echo "If your connection is fine, the Firefox version may be too old and no longer available on TaskCluster."
  echo "See https://github.com/openwpm/OpenWPM/issues/964 for more details."
  exit 1
fi

case "$(uname -s)" in
Darwin)
  rm -rf Nightly.app || true
  hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp target.dmg
  cp -r /Volumes/firefox-tmp/Nightly.app .
  hdiutil detach /Volumes/firefox-tmp
  rm target.dmg
  ;;
Linux)
  if ! tar Jxf target.tar.xz; then
    echo "Error: Failed to extract Firefox archive."
    exit 1
  fi
  rm -rf firefox-bin
  mv firefox firefox-bin
  rm target.tar.xz
  ;;
esac

echo 'Firefox succesfully installed'
