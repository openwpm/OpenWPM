---
title: "Custom storage table via test_custom_function (no schema.sql pollution)"
tags: ["pattern-library", "storage", "testing", "design-doc"]
sources: []
contributors: ["claude"]
created: 2026-06-14
updated: 2026-06-14
---


## Design Specification

### problem

You need a crawl/command to write rows into a NEW table (not one of the schemas in
`openwpm/storage/schema.sql`) and then assert on those rows from a test, WITHOUT
polluting `schema.sql` / `parquet_schema.py` and WITHOUT inventing a new storage
provider or cross-process readback.

### proven pattern: test_custom_function

Reference: `test/test_custom_function_command.py::test_custom_function`.

The crawl SQLite DB on disk is the cross-process channel. The OS file is shared by
every process; no pickling, no `multiprocess.Queue`, no in-memory handle.

1. **Test creates the table directly in the crawl DB** before launching the manager:

   ```python
   path = manager_params.data_directory / "crawl-data.sqlite"
   db = sqlite3.connect(path)
   cur = db.cursor()
   cur.execute(
       "CREATE TABLE IF NOT EXISTS %s ("
       "  top_url TEXT, link TEXT, visit_id INTEGER, browser_id INTEGER);" % table_name
   )
   cur.close(); db.close()
   ```

2. **The command sends records to the storage controller over the socket**, naming
   the table. The controller's StructuredStorageProvider INSERTs into the
   already-existing table:

   ```python
   sock = ClientSocket()
   sock.connect(*manager_params.storage_controller_address)
   sock.send("custom_command")
   sock.send((table_name, {"top_url": ..., "link": ..., "visit_id": visit_id, "browser_id": browser_id}))
   sock.close()
   ```

   (In real commands prefer the `extension_socket` / `DataSocket.store_record`
   already passed into `execute()`; the test above opens its own `ClientSocket` to
   the `manager_params.storage_controller_address`.)

3. **The test queries the table AFTER `manager.close()`** (shutdown flushes the
   storage controller to disk), using `db_utils.query_db`:

   ```python
   manager.execute_command_sequence(cs)
   manager.close()
   rows = db_utils.query_db(path, "SELECT top_url, link FROM page_links;", as_tuple=True)
   assert EXPECTED == set(rows)
   ```

### why not memorystructuredprovider.handle.poll_queue() for end-to-end crawls

`MemoryStructuredProvider` + `MemoryProviderHandle.poll_queue()`
(`openwpm/storage/in_memory_storage.py`) is built for IN-PROCESS storage-controller
unit tests (`test/storage/test_storage_controller.py`), where the test constructs the
handle, spawns the controller, and holds the SAME parent-side reference.

It is the WRONG tool for a `TaskManager`-driven end-to-end crawl because:

- `StorageControllerHandle.launch()` runs `StorageController.run` in a SEPARATE
  `Process` (`openwpm/storage/storage_controller.py` ~line 496). The provider object
  is copied into the child; records get put on the child's queue copy.
- `TaskManager` exposes only `storage_controller_handle`; there is NO supported public
  path from a `TaskManager` crawl back to `structured_storage_provider.handle`. So
  `poll_queue()` on a parent-side handle reads an empty queue -> records never arrive
  -> tests fail intermittently/permanently. (This is the #1154 detection-results
  incident: 7 CI failures + a burned verify worker.)

Use the on-disk SQLite table pattern above for anything that goes through a real
`TaskManager` crawl.

### checklist

- [ ] New table created with `CREATE TABLE IF NOT EXISTS` in the test (or a migration),
      NOT added to `schema.sql`.
- [ ] Records sent over the storage-controller socket, tagged with the table name.
- [ ] Assertions run AFTER `manager.close()`, via `db_utils.query_db`.
- [ ] No `MemoryStructuredProvider`/`poll_queue` for `TaskManager` end-to-end crawls.

