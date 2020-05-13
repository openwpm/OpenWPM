TAG=25e0edbb0a613c3bf794c93ba3aa0985d29d5ef4
UNBRANDED_RELEASE_MAC_BUILD="https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/gecko.v2.mozilla-release.revision.$TAG.firefox.macosx64-add-on-devel/artifacts/public/build/target.dmg"
wget "$UNBRANDED_RELEASE_MAC_BUILD"
# Install unbranded release ff
rm -rf Nightly.app || true
hdiutil attach -nobrowse -mountpoint /Volumes/firefox-tmp target.dmg
cp -r /Volumes/firefox-tmp/Nightly.app .
hdiutil detach /Volumes/firefox-tmp
rm target.dmg