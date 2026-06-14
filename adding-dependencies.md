---
title: "Adding dependencies: use repin.sh, never hand-edit environment.yaml"
tags: ["deps", "conda", "procedure"]
sources: []
contributors: ["claude"]
created: 2026-06-14
updated: 2026-06-14
---

To add or change a Python/conda dependency, NEVER hand-edit `environment.yaml` — it is GENERATED.

Procedure:
1. Edit `scripts/environment-unpinned.yaml` (runtime deps) or `scripts/environment-unpinned-dev.yaml` (dev/test deps, e.g. pytest plugins).
2. Run `scripts/repin.sh`. It builds the env from the unpinned specs and `conda env export --no-builds --override-channels -c conda-forge`s the fully-solved result into the pinned `environment.yaml` (correct format, channels, transitive pins).

Hand-pinning a line like `pytest-rerunfailures=16.3` directly into `environment.yaml` is WRONG: it isn't a real conda solve, omits transitive pins, and desyncs from what repin produces. CI builds from `environment.yaml`, so it must be repin-generated.

CAVEAT (destructive): `repin.sh` runs `conda env create`, which REMOVES and recreates the shared `openwpm` conda env (same footgun as bare `install.sh`). Do NOT run it while other workers are using the shared env (e.g. running browser tests) — it'll clobber them mid-run. Run it when env-dependent work is quiesced.
