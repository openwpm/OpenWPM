# Architecture Internals

This document describes OpenWPM's internal architecture in detail: process
model, communication channels, timeouts, and coupling points. For a high-level
overview, see [Platform-Architecture.md](Platform-Architecture.md).

## Process Model

```
Main Process (TaskManager)
  ├── StorageController Process (asyncio TCP server)
  │   ├── StructuredStorageProvider (SQLite/Parquet/S3/GCS)
  │   └── UnstructuredStorageProvider (LevelDB/Gzip/S3/GCS)
  ├── BrowserManager Process 1..N
  │   ├── Selenium WebDriver → Firefox
  │   └── WebExtension (HTTP/Cookie/JS/Nav/DNS instrumentation)
  ├── MPLogger Process (log aggregation)
  └── Watchdog Threads (memory/process monitoring)
```

The **TaskManager** is the user-facing entry point. It spawns:

- A **StorageController** in a child process, which runs an asyncio TCP server
  to receive data from both the WebExtension (JSON serialization) and the
  TaskManager itself (dill serialization via `DataSocket`).
- One or more **BrowserManager** child processes, each driving a Firefox instance
  via Selenium WebDriver. Each browser loads the OpenWPM WebExtension for
  instrumentation.
- An **MPLogger** thread for centralized log aggregation.
- **Watchdog threads** for memory and process monitoring.

## Communication Channels

| Channel | Direction | Mechanism | Pattern |
|---------|-----------|-----------|---------|
| TaskManager → BrowserManager | `command_queue` (`mp.Queue`) | Request (one command at a time) |
| BrowserManager → TaskManager | `status_queue` (`mp.Queue`) | Reply (`"OK"` / `"FAILED"` / `"CRITICAL"` / `"NETERROR"`) |
| Extension → StorageController | TCP socket (JSON) | Fire-and-forget |
| TaskManager → StorageController | `DataSocket` (TCP, dill) | Fire-and-forget |
| StorageController → TaskManager | `status_queue` (`mp.Queue`) | Periodic push (every 5s) |
| StorageController → TaskManager | `completion_queue` (`mp.Queue`) | Polled by callback thread (every 1s/5s) |
| TaskManager → StorageController | `shutdown_queue` (`mp.Queue`) | One-shot signal |
| Extension startup → BrowserManager | File-based (`extension_port.txt`) | Polling every 0.1s for 5s |

**Key observation**: No channel supports bidirectional communication. The
`status_queue` between BrowserManager and TaskManager is the closest, but it's
strictly request-reply: TaskManager sends one command, then blocks waiting for
exactly one status response.

## Socket Wire Protocol and Security

Both the Extension → StorageController data channel and the reverse
TaskManager → Extension control channel use the same length-prefixed framing
(`openwpm/socket_interface.py`, `Extension/bundled/privileged/sockets/api.js`):
a 5-byte header (`>Lc` = big-endian `uint32` byte length + 1-byte serialization
tag) followed by the payload. The tag is one of `n` (raw bytes), `u` (UTF-8
string), `j` (JSON), or `d` (dill pickle). Payloads are framed on the **payload
byte length** (UTF-8 bytes for the `j`/`u` text frames; raw bytes for the `n`
and `d` binary frames — the `d` dill pickles are not UTF-8), and the length
field rejects payloads ≥ 4 GiB rather than
silently truncating.

### Security model (single-tenant assumption)

The sockets are **loopback-only** (`StorageController` binds
`("localhost", 0)`; the extension listener uses `init(-1, true, -1)`), bound to
**random ephemeral ports** exchanged out-of-band via the profile directory, and
**not reachable from web content or off-host**. They are, however,
**unauthenticated** — there is no per-connection token, and the first client
message is just a name string.

Consequently, any **local process running as the same (or a more privileged)
user** can, while a port is open, inject or forge framed records — and a forged
`d` (dill) frame is deserialized via `dill.loads`, an **arbitrary-code-execution
primitive** in the StorageController process. This is **acceptable for
single-tenant deployments** (the typical measurement host) but a **real risk on
shared / multi-tenant hosts**. The wire protocol is intentionally left
unchanged; hardening (auth token / dropping dill on the wire) is tracked in
[#1179](https://github.com/openwpm/OpenWPM/issues/1179).

## Timeout Inventory

| Location | Timeout | Purpose |
|----------|---------|---------|
| `BrowserManagerHandle._SPAWN_TIMEOUT` | 120s | Browser spawn per attempt |
| `CommandSequence.get()` default | 60s | Page navigation |
| `CommandSequence.screenshot()` default | 30s | Screenshot capture |
| `CommandSequence.dump_profile()` default | 120s | Profile archiving |
| `BrowserManager._start_extension` | 5s | Find `extension_port.txt` |
| `BrowserManager._start_extension` | 10s | Find `OPENWPM_STARTUP_SUCCESS.txt` |
| `BrowserManagerHandle.close_browser_manager` | 30s | Webdriver shutdown response |
| `BrowserManagerHandle.close_browser_manager` | 30s | Browser process exit |
| `StorageController.STATUS_TIMEOUT` | 120s | Storage status heartbeat |
| `StorageController.BATCH_COMMIT_TIMEOUT` | 30s | Flush if idle |
| `StorageController.STATUS_UPDATE_INTERVAL` | 5s | Status push interval |
| `StorageController.update_completion_queue` | 5s | Completion poll interval |
| `_mark_command_sequences_complete` | 1s | Callback thread poll |
| `BrowserManagerHandle.execute_command_sequence` | 2s | Post-sequence drain sleep |
| `FinalizeCommand.execute` | 5s | Extension buffer drain |
| Watchdog | 10s | Check interval |
| Process watchdog buffer | 300s | Avoid killing fresh browsers |

## Coupling Analysis

### BrowserManagerHandle ↔ TaskManager

`BrowserManagerHandle.execute_command_sequence` (in `openwpm/browser_manager.py`)
takes a `TaskManager` reference and directly accesses these internal fields:

- `task_manager.sock` — `DataSocket` for recording crawl history
- `task_manager.failure_status` — `dict`, set on critical errors
- `task_manager.failure_count` — `int`, incremented on failures
- `task_manager.threadlock` — `threading.Lock`
- `task_manager.closing` — `bool`
- `task_manager.failure_limit` — `int`
- `task_manager.sock.finalize_visit_id()` — visit lifecycle management

This creates a circular dependency: `TaskManager` imports `BrowserManagerHandle`,
and `BrowserManagerHandle` uses `TaskManager` (via `TYPE_CHECKING` forward ref).

### BaseCommand Coupling

Commands (in `openwpm/commands/types.py`) require concrete types: `Firefox`
webdriver, `BrowserParamsInternal`, `ManagerParamsInternal`, `ClientSocket`.
Commands cannot be executed without a real browser and extension socket.

### TaskManager.__init__ Sequencing

The constructor performs all initialization sequentially: validates config →
starts MPLogger → launches StorageController → initializes browsers → launches
browsers → starts watchdog → starts storage logger → saves config → starts
callback thread. Any test touching TaskManager must pay all these costs.
