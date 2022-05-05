# Release Checklist

We aim to release a new version of OpenWPM with each new Firefox release (~1 release per month). The following steps are necessary for a release:

1. Upgrade Firefox to the newest version.
    1. Go to: <https://hg.mozilla.org/releases/mozilla-release/tags>.
    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
    3. Update the `TAG` variable in [`scripts/install-firefox.sh`](../scripts/install-firefox.sh#L12) to that hash and the comment to the new tag name.
2. Run `./scripts/update.sh`
3. Increment the version number in [VERSION](../VERSION)
4. Add a summary of changes since the last version to [CHANGELOG](../CHANGELOG.md)
5. Squash and merge the release PR to master.
6. Publish a new release from <https://github.com/openwpm/OpenWPM/releases>:
    1. Click "Draft a new release".
    2. Enter the "Tag version" and "Release title" as `vX.X.X`.
    3. In the description:
        1. Include the text `Updates OpenWPM to Firefox X` if this release is also a new FF version.
        2. Include a link to the CHANGELOG, e.g. `See the [CHANGELOG]() for details.`.
