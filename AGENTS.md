# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

OpenWPM is a web privacy measurement framework for conducting large-scale privacy studies (thousands to millions of websites). Built on Firefox with Selenium automation, it captures HTTP traffic, JavaScript API calls, cookies, navigation, and DNS queries through a privileged WebExtension.

## Build & Development Commands

### Initial Setup
```bash
./install.sh  # Creates conda env, installs Firefox, builds extension
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_storage.py -v

# Run tests matching pattern
pytest -k "test_http" -v

# Run tests by marker
pytest -m pyonly  # Python-only tests (no browser)
pytest -m slow    # Slow tests
```

### Linting & Formatting

**Python:**
```bash
pre-commit run --all-files  # Run all hooks
black .                      # Format Python
isort .                      # Sort imports
mypy openwpm                 # Type checking
```

**Extension (from Extension/ directory):**
```bash
npm run lint    # ESLint + Prettier + web-ext lint
npm run fix     # Auto-fix issues
npm run build   # Rebuild extension (TypeScript → webpack → web-ext)
```

### Rebuilding Extension
```bash
scripts/build-extension.sh
# Or from Extension/: npm run build
```

### Updating Dependencies
```bash
scripts/repin.sh  # Don't edit environment.yaml directly
```

## Architecture

```
TaskManager (orchestrator)
├── BrowserManagerHandle[] → BrowserManager (per-browser process)
│                              └── Selenium WebDriver → Firefox + WebExtension
└── StorageController (isolated process)
    ├── StructuredStorageProvider (SQLite/Parquet/S3/GCS)
    └── UnstructuredStorageProvider (LevelDB/Gzip/S3/GCS)
```

### Core Components

- **TaskManager** (`openwpm/task_manager.py`): Orchestrates browsers, manages command queues, runs watchdogs for crash recovery
- **BrowserManager** (`openwpm/browser_manager.py`): Wraps Selenium, executes commands, handles browser lifecycle
- **WebExtension** (`Extension/src/`): TypeScript extension collecting HTTP, cookies, JS calls, navigation via privileged browser APIs
- **Storage System** (`openwpm/storage/`): Receives data from extension via sockets, writes to configured backends
- **Commands** (`openwpm/commands/`): Extend `BaseCommand` with `execute()` method

### Configuration

- `ManagerParams`: Platform settings (num_browsers, data_directory, log_path)
- `BrowserParams`: Per-browser settings (instrumentation flags, display mode, profile handling)
- Both defined in `openwpm/config.py` with validation functions
- See [docs/Configuration.md](docs/Configuration.md) for full details

### Known Issues

- `callstack_instrument` is broken — enabling it raises `ConfigError`. See [#557](https://github.com/openwpm/OpenWPM/issues/557).

### Large Test Fixtures (jj users)

`test/profile.tar.gz` (~2.5MB) exceeds jj's default `snapshot.max-new-file-size` (1MB). jj will silently show it as deleted and exclude it from commits. **Do NOT increase the snapshot limit.** If `jj status` shows `D test/profile.tar.gz`, restore it from the parent: `jj restore --from @- test/profile.tar.gz`. This file is a static test fixture and should never be modified unless explicitly requested.

### Data Schema

Schema files must be kept in sync:
- `openwpm/storage/schema.sql` (SQLite)
- `openwpm/storage/parquet_schema.py` (Parquet)

## Scratch Space

Use `datadir/` (project root) for any temporary or scratch data — crawl outputs, test databases, logs, etc. This directory is gitignored and is the conventional location for local data. Do not use `/tmp`, `~`, or other locations outside the project.

`demo.py` defaults to writing here (`manager_params.data_directory = Path("./datadir/")`). The directory is created on demand.

## Release Process

When creating releases, PRs, or interacting with GitHub, prefer using the `gh` CLI over the web UI.

## Key Files

- `demo.py`: Reference implementation showing typical usage
- `custom_command.py`: Example of custom command implementation
- `test/manual_test.py`: Interactive debugging (`python -m test.manual_test --selenium`)

## Display Modes

- `native`: GUI visible (default)
- `headless`: Firefox headless (no X server needed)
- `xvfb`: X virtual framebuffer (full browser, no GUI, for servers)
