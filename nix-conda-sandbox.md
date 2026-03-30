---
title: "Nix shell.nix for conda-based projects in crosslink-sandbox"
tags: [nix, conda, sandbox]
sources:
  - url: research-issue-12
    title: ""
    accessed_at: 2026-03-30
contributors: [research-shell-nix]
created: 2026-03-30
updated: 2026-03-30
---

## Problem
crosslink-sandbox (bubblewrap) doesn't mount ~/.conda, so conda environments aren't accessible inside sandboxed agents. OpenWPM uses conda (environment.yaml) for its Python 3.14 env.

## Working Solution: shell.nix with nix fallback
A shell.nix at project root is auto-detected by crosslink-sandbox. Two modes:

1. **Preferred: .conda-env prefix** — Run `conda create --prefix .conda-env -f environment.yaml` outside sandbox. shell.nix adds `.conda-env/bin` to PATH. Works because project dir is already mounted rw.

2. **Fallback: pure nix** — nixpkgs python314 (3.14.3) with ~25 packages. Missing: gcsfs, s3fs (cfn-lint py3.14 issue), domain-utils, tranco, pytest-split. Sufficient for most agent tasks.

## Key Facts
- nixpkgs has python314 (3.14.3) with good package coverage
- ~/.conda is on tmpfs, project dir on ZFS — different filesystems, no hardlinks
- conda create --prefix makes a standalone env inside the project dir
- Sandbox HOME is tmpfs — no persistent home state between runs
- Firefox at project_root/firefox-bin/firefox-bin (from install-firefox.sh)
- Nix provides: git, gh, nodejs, geckodriver, pre-commit, leveldb

## Verified Working Inside Sandbox (nix fallback)
python3 3.14.3, git 2.53.0, gh 2.88.1, node 24.14.0, pytest 9.0.2, pre-commit 4.5.1, selenium 4.40.0, `import openwpm` OK.

## Future: .sandbox.json for full conda support
~25-line change to crosslink-sandbox to read .sandbox.json for extra bind mounts. Would enable mounting ~/.conda read-only and using `conda run` directly.
