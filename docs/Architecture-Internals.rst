Architecture Internals
======================

This document describes OpenWPM's internal architecture in detail: process
model, communication channels, timeouts, and coupling points. For a high-level
overview, see :doc:`Platform-Architecture`.

Process Model
-------------

.. code-block:: text

   Main Process (TaskManager)
     ├── StorageController Process (asyncio TCP server)
     │   ├── StructuredStorageProvider (SQLite/Parquet/S3/GCS)
     │   └── UnstructuredStorageProvider (LevelDB/Gzip/S3/GCS)
     ├── BrowserManager Process 1..N
     │   ├── Selenium WebDriver → Firefox
     │   └── WebExtension (HTTP/Cookie/JS/Nav/DNS instrumentation)
     ├── MPLogger Process (log aggregation)
     └── Watchdog Threads (memory/process monitoring)

The :py:class:`~openwpm.task_manager.TaskManager` is the user-facing entry
point. It spawns:

- A :py:class:`~openwpm.storage.storage_controller.StorageController` in a
  child process, which runs an asyncio TCP server to receive data from both
  the WebExtension (JSON serialization) and the ``TaskManager`` itself (dill
  serialization via :py:class:`~openwpm.storage.storage_controller.DataSocket`).
- One or more :py:class:`~openwpm.browser_manager.BrowserManager` child
  processes, each driving a Firefox instance via Selenium WebDriver. Each
  browser loads the OpenWPM WebExtension for instrumentation.
- An :py:class:`~openwpm.mp_logger.MPLogger` thread for centralized log
  aggregation.
- **Watchdog threads** for memory and process monitoring.

Why a process per browser? See the *multi-process model* entry in
:doc:`design-principles` for the historical reasoning and guidance for
future refactors.

Communication Channels
----------------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Channel
     - Mechanism
     - Pattern
   * - TaskManager → BrowserManager
     - ``command_queue`` (``mp.Queue``)
     - Request (one command at a time)
   * - BrowserManager → TaskManager
     - ``status_queue`` (``mp.Queue``)
     - Reply (``"OK"`` / ``"FAILED"`` / ``"CRITICAL"`` / ``"NETERROR"``)
   * - Extension → StorageController
     - TCP socket (JSON)
     - Fire-and-forget
   * - TaskManager → StorageController
     - :py:class:`~openwpm.storage.storage_controller.DataSocket` (TCP, dill)
     - Fire-and-forget
   * - StorageController → TaskManager
     - ``status_queue`` (``mp.Queue``)
     - Periodic push (every 5s)
   * - StorageController → TaskManager
     - ``completion_queue`` (``mp.Queue``)
     - Polled by callback thread (every 1s/5s)
   * - TaskManager → StorageController
     - ``shutdown_queue`` (``mp.Queue``)
     - One-shot signal
   * - Extension startup → BrowserManager
     - File-based (``extension_port.txt``)
     - Polling every 0.1s for 5s

**Key observation**: No channel supports bidirectional communication. The
``status_queue`` between ``BrowserManager`` and ``TaskManager`` is the
closest, but it is strictly request-reply: ``TaskManager`` sends one command,
then blocks waiting for exactly one status response.

Design Rationale
----------------

Why these process boundaries and channels exist. Several of these decisions
trace to the trust model in :doc:`design-principles`.

Why StorageController is a separate process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:py:class:`~openwpm.storage.storage_controller.StorageController` runs in its
own process, not as a thread of :py:class:`~openwpm.task_manager.TaskManager`.
Two reasons:

- ``TaskManager`` lives in a process the researcher controls. A custom
  command — or any researcher code in that process — can hold the GIL or
  block, which would stall a storage thread sharing it. A separate process is
  insulated from that.
- ``StorageController`` runs its own asyncio event loop. Running a second
  asyncio runtime alongside another in the same process is unsupported and
  unpredictable; a dedicated process avoids the question entirely.

Why the extension talks to StorageController directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The WebExtension sends captured data straight to ``StorageController`` rather
than routing it through its ``BrowserManager``:

- Legacy: this is how the data path has long been wired.
- ``BrowserManager`` runs researcher-controlled command code. Routing the
  data path through it would send every captured record past untrusted code.
- Proxying is messy regardless: ``BrowserManager`` would either forward bytes
  blindly (pure indirection, no value) or parse and re-serialize every record
  at the hop (wasteful).

Why sockets here and ``mp.Queue`` there
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OpenWPM uses both ``mp.Queue`` and TCP sockets for inter-process
communication. The rule:

- **Use** ``mp.Queue`` **when both endpoints are Python processes spawned by**
  ``multiprocessing`` **and the channel's topology is static** — one fixed
  peer for the channel's lifetime. The ``TaskManager`` ↔ ``BrowserManager``
  command/status channels fit this: both ends are Python, and each channel
  serves exactly one browser.
- **Use a socket when an endpoint is not such a process, or the peer set is
  dynamic.** The WebExtension is JavaScript inside Firefox — it cannot use a
  Python ``mp.Queue`` at all, so its channel to ``StorageController`` *must*
  be a socket. Browsers are also restarted regularly, so the set of peers a
  long-lived ``StorageController`` talks to changes over time; sockets model
  "a peer connected / a peer went away" natively via accept and close, where
  an ``mp.Queue`` does not.

Reaching for ``mp.Queue`` on a dynamic-peer channel leads to passing queue
handles through queues and dispatching per-peer handler routines — which is
just a worse socket. The split above is the principled version of that
observation.

Why the extension-startup handshake is file-based
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On startup the extension discovers its ``BrowserManager`` by reading a port
number from a file (``extension_port.txt``) in the browser profile directory,
rather than being told a port directly.

- The extension cannot know its ``BrowserManager``'s socket a priori — there
  is no channel to tell it before the socket exists.
- Assigning a fixed port via configuration would risk losing the
  port-acquisition race to an unrelated process on the machine.

So ``BrowserManager`` binds an ephemeral port, writes it where the extension
will look, and the extension polls for the file. This favors robustness over
simplicity.

Historical note: the privileged socket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OpenWPM's data path uses a privileged socket implementation rather than
WebSockets or HTTP. This traces to an early-maintainer view that raw sockets
are simple, and to the fact that the data collector and storage layer began
life as a network proxy — only later morphing into the browser extension that
exists today. The privileged-socket machinery is a survival of that proxy
ancestry.

Timeout Inventory
-----------------

.. list-table::
   :header-rows: 1
   :widths: 45 12 43

   * - Location
     - Timeout
     - Purpose
   * - ``BrowserManagerHandle._SPAWN_TIMEOUT``
     - 120s
     - Browser spawn per attempt
   * - ``CommandSequence.get()`` default
     - 60s
     - Page navigation
   * - ``CommandSequence.save_screenshot()`` default
     - 30s
     - Screenshot capture
   * - ``CommandSequence.dump_profile()`` default
     - 120s
     - Profile archiving
   * - ``BrowserManager._start_extension``
     - 5s
     - Find ``extension_port.txt``
   * - ``BrowserManager._start_extension``
     - 10s
     - Find ``OPENWPM_STARTUP_SUCCESS.txt``
   * - ``BrowserManagerHandle.close_browser_manager``
     - 30s
     - Webdriver shutdown response
   * - ``BrowserManagerHandle.close_browser_manager``
     - 30s
     - Browser process exit
   * - ``StorageController.STATUS_TIMEOUT``
     - 120s
     - Storage status heartbeat
   * - ``StorageController.BATCH_COMMIT_TIMEOUT``
     - 30s
     - Flush if idle
   * - ``StorageController.STATUS_UPDATE_INTERVAL``
     - 5s
     - Status push interval
   * - ``StorageController.update_completion_queue``
     - 5s
     - Completion poll interval
   * - ``_mark_command_sequences_complete``
     - 1s
     - Callback thread poll
   * - ``BrowserManagerHandle.execute_command_sequence``
     - 2s
     - Post-sequence drain sleep
   * - ``FinalizeCommand.execute``
     - 5s
     - Extension buffer drain
   * - Watchdog
     - 10s
     - Check interval
   * - Process watchdog buffer
     - 300s
     - Avoid killing fresh browsers

Coupling Analysis
-----------------

OpenWPM's components are tightly coupled today. This is a recognized design
flaw — see the *reduce coupling between components* principle in
:doc:`design-principles`. The specific coupling points are catalogued below so
that work in this area has a concrete starting list.

BrowserManagerHandle ↔ TaskManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:py:meth:`~openwpm.browser_manager.BrowserManagerHandle.execute_command_sequence`
takes a :py:class:`~openwpm.task_manager.TaskManager` reference and directly
accesses these internal fields:

- ``task_manager.sock`` — ``DataSocket`` for recording crawl history
- ``task_manager.failure_status`` — ``dict``, set on critical errors
- ``task_manager.failure_count`` — ``int``, incremented on failures
- ``task_manager.threadlock`` — ``threading.Lock``
- ``task_manager.closing`` — ``bool``
- ``task_manager.failure_limit`` — ``int``
- ``task_manager.sock.finalize_visit_id()`` — visit lifecycle management

This creates a circular dependency:
:py:class:`~openwpm.task_manager.TaskManager` imports
:py:class:`~openwpm.browser_manager.BrowserManagerHandle`, and
``BrowserManagerHandle`` uses ``TaskManager`` (via a ``TYPE_CHECKING`` forward
reference).

BaseCommand Coupling
~~~~~~~~~~~~~~~~~~~~

Commands derived from :py:class:`~openwpm.commands.types.BaseCommand` require
concrete types: a ``Firefox`` webdriver,
:py:class:`~openwpm.config.BrowserParamsInternal`,
:py:class:`~openwpm.config.ManagerParamsInternal`, and a
:py:class:`~openwpm.socket_interface.ClientSocket`. Commands cannot be
executed without a real browser and extension socket.

TaskManager.__init__ Sequencing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:class:`~openwpm.task_manager.TaskManager` constructor performs all
initialization sequentially: validates config → starts ``MPLogger`` →
launches ``StorageController`` → initializes browsers → launches browsers →
starts watchdog → starts storage logger → saves config → starts callback
thread. Any test touching ``TaskManager`` must pay all of these costs.

Implications for Custom Commands
--------------------------------

The multi-process model has a consequence that regularly surprises
researchers writing custom commands: **a command does not run in the main
process.** It runs in the :py:class:`~openwpm.browser_manager.BrowserManager`
subprocess that owns its browser.

Therefore:

- Module-level or global state mutated inside a command is mutated in the
  ``BrowserManager`` process. Those changes are **not** visible back in the
  :py:class:`~openwpm.task_manager.TaskManager` process.
- The classic mistake: create a list (or dict) in the main process, append to
  it from within a command, and find it empty when the crawl ends. The
  appends happened in another process's copy of that object.

To get data out of a command, use a channel that crosses the process
boundary:

- Write results to the database — the normal path, and what the storage
  pipeline exists for.
- Or, if data must be handed back in-process, pass an explicit
  ``multiprocessing.Queue`` handle into the command and read from it.

Do not use shared global state as a communication channel; it will not be
reflected back.
