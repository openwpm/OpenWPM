# Release Checklist

We aim to release a new version of OpenWPM with each new Firefox release (~1 release per month). The following steps are necessary for a release:

1. Run `python scripts/update.py` — this will:
    - Repin the conda environment
    - Sync linter versions in `.pre-commit-config.yaml` to match `environment.yaml` (black, isort, mypy)
    - Sync `engines.node` in `Extension/package.json` to match the conda `nodejs` version (the Extension is only built inside this project, so the engines field documents what we test against rather than a public compatibility floor)
    - Bump `VERSION` to next-minor after the latest `v*` git tag if it has drifted behind (catches the case where a release was tagged but `VERSION` was never bumped — historically happened between v0.32.0 and v0.33.0)
    - Bump all npm dependencies to their latest compatible versions
    - Rebuild the extension
    - Automatically detect and apply any new Firefox release to `scripts/install-firefox.sh` and pin `applications.gecko.strict_min_version` in `Extension/bundled/manifest.json` to that major (each release ships only with the bundled Firefox, so the floor should match)
2. **Before** raising the Firefox pin from N-1 to N, regenerate the seed profile
   fixture so the bump PR's CI exercises a real cross-version profile-compatibility
   check. The seed profile (`test/profile.tar.gz`) exists to confirm that Firefox N
   can read a profile primed by the *previous* Firefox (N-1) and that a baked-in
   extension still starts up after restoration. To regenerate, run the script with
   the **previous** stable Firefox still on `FIREFOX_BINARY`, then commit the result:

   ```bash
   export FIREFOX_BINARY=/path/to/firefox-N-1/firefox-bin
   python scripts/regenerate-test-profile.py
   ```

   The script installs uBlock Origin from AMO (the only live addons.mozilla.org
   call; CI never touches AMO) and dumps the profile. The regenerated tar exceeds
   jj's default `snapshot.max-new-file-size`; because the file already exists in
   history, jj snapshots the modification anyway — verify it lands in the commit
   with `jj diff --stat` (it should appear as a binary modification, not `D`). Do
   **not** raise the snapshot limit globally. See the script header for full details.
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
