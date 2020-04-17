# Use the Unbranded build that corresponds to a specific Firefox version 
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.
TAG=25e0edbb0a613c3bf794c93ba3aa0985d29d5ef4
UNBRANDED_RELEASE_LINUX_BUILD="https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/gecko.v2.mozilla-release.revision.$TAG.firefox.linux64-add-on-devel/artifacts/public/build/target.tar.bz2"
wget "$UNBRANDED_RELEASE_LINUX_BUILD"
tar jxf target.tar.bz2
rm -rf firefox-bin
mv firefox firefox-bin
rm target.tar.bz2