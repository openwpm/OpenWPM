We aim to release a new version of OpenWPM with each new Firefox release (~1 release per month). The following steps are necessary for a release

1. Upgrade Firefox to the newest version.
    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
    3. Update the `TAG` variable in [`scripts/install-firefox.sh`](https://github.com/mozilla/OpenWPM/blob/5ffde00ecd5ecaa9105b74935490e5e267596eb7/scripts/install-firefox.sh#L12) to that hash and the comment to the new tag name.
2. Update extension dependencies.
    1. Run `npm update` in `automation/Extension/firefox`.
    2. Run `npm update` in `automation/Extension/webext-instrumentation`.
3. Update python and system dependencies by following the ["managing requirements" instructions](https://github.com/mozilla/OpenWPM#managing-requirements).
4. Increment the version number in [VERSION](https://github.com/mozilla/OpenWPM/blob/master/VERSION)
5. Add a summary of changes since the last version to [CHANGELOG](https://github.com/mozilla/OpenWPM/blob/master/CHANGELOG.md)
6. Squash and merge the release PR to master.
7. Publish a new release from https://github.com/mozilla/OpenWPM/releases:
    1. Click "Draft a new release".
    2. Enter the "Tag version" and "Release title" as `vX.X.X`.
    3. In the description:
        1. Include the text `Updates OpenWPM to Firefox X` if this release is also a new FF version.
        2. Include a link to the CHANGELOG, e.g. `See the [CHANGELOG]() for details.`.