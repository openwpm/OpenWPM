---
title: "JJ worktree: browser-test setup"
tags: ["worktree", "setup", "testing"]
sources: []
contributors: ["claude"]
created: 2026-06-14
updated: 2026-06-14
---

To make a fresh jj worktree (`jj workspace add ...`) able to run OpenWPM browser tests, run from the worktree root:

    ./install.sh --skip-create

This downloads `firefox-bin` LOCALLY into the worktree and builds the extension xpi, WITHOUT touching the shared conda env. After it, `get_firefox_binary_path()` finds the worktree's own `firefox-bin` (no `FIREFOX_BINARY` needed).

**CRITICAL: never run bare `./install.sh` in a worktree.** Its header states "This script will remove an existing openwpm conda environment if it exists" — bare `install.sh` REMOVES and recreates the shared `openwpm` conda env that ALL workspaces depend on. Always pass `--skip-create`.

Already shared (no setup needed): the conda env is active; `import openwpm` resolves to the worktree's own source (no editable-install trap); `geckodriver` is on PATH.

Lean alternative (avoids re-downloading Firefox per worktree): `export FIREFOX_BINARY=<main-repo>/firefox-bin/firefox-bin` (absolute) + `(cd Extension && npm ci && npm run build)`.
