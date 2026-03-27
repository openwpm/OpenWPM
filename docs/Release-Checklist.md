# Release Checklist

We aim to release a new version of OpenWPM with each new Firefox release (~1 release per month). The following steps are necessary for a release:

1. Run `python scripts/update.py` — this will:
    - Repin the conda environment
    - Bump all npm dependencies to their latest compatible versions
    - Rebuild the extension
    - Automatically detect and apply any new Firefox release to `scripts/install-firefox.sh`
2. Check if we can unpin our python version (this requires Linux to test) See <https://github.com/openwpm/OpenWPM/issues/1111>
3. Run `./scripts/install-firefox.sh` to install the updated Firefox locally and verify the test suite passes.
4. Increment the version number in [VERSION](../VERSION)
5. Add a summary of changes since the last version to [CHANGELOG](../CHANGELOG.md)
6. Squash and merge the release PR to master.
7. Publish a new release from <https://github.com/openwpm/OpenWPM/releases>:
    1. Click "Draft a new release".
    2. Enter the "Tag version" and "Release title" as `vX.X.X`.
    3. In the description:
        1. Include the text `Updates OpenWPM to Firefox X` if this release is also a new FF version.
        2. Include a link to the CHANGELOG, e.g. `See the [CHANGELOG]() for details.`.
