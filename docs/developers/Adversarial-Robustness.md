# Adversarial robustness of the crawl pipeline

OpenWPM is built to crawl thousands-to-millions of untrusted, often hostile web
pages. The pipeline must therefore **degrade gracefully** under adversarial
conditions rather than hang, lose data silently, or stop making progress.

This document describes the adversarial / chaos test suite and the robustness
gaps it surfaced.

## The graceful-degradation property

For every adversarial condition, the pipeline must guarantee:

1. **Forward progress** — every visit that is *started* reaches a terminal
   state, and the crawl continues to the next site.
2. **No silent data loss** — the offending visit is accounted for (completion
   queue entry / `incomplete_visits` row), and prior visits' data survives.
3. **No hang** — recovery happens within the per-command timeout plus the
   browser restart budget.
4. **Recovery continues the crawl** — the watchdog / `BrowserManager` restart
   path brings the browser back and subsequent sites are visited.

## Test suite

| File | Tier | Browser? |
|---|---|---|
| `test/storage/test_adversarial_storage_controller.py` | StorageController + providers, driven in-process via a real subprocess + `DataSocket` | no (`pyonly`) |
| `test/storage/test_adversarial_socket.py` | Wire protocol / asyncio server | no (`pyonly`) |
| `test/test_adversarial_pipeline.py` | Full `TaskManager` → `BrowserManager` → Firefox recovery | **yes** |

The browser-free tests follow the in-process driving pattern of
`test/storage/test_storage_controller.py`. The browser-required tests are
guarded by a `requires_browser` skip (resolved via the same logic as
`get_firefox_binary_path`) so they skip cleanly where no launchable Firefox is
present and run for real in CI (pinned unbranded Firefox + built xpi). They are
not faked.

### Scenarios

| # | Scenario | Where | Status |
|---|---|---|---|
| S1a | Custom command `execute()` raises | `test_adversarial_pipeline` | recovery asserted (CI) |
| S1b | Custom command hangs forever | `test_adversarial_pipeline` | timeout+kill asserted (CI) |
| S2 | Crashing extension modification | (design item, see below) | not implemented |
| S3 | Socket-level hostility (truncated / garbage / oversized / wrong-arity frames, mid-message disconnect) | `test_adversarial_socket` | **SURVIVES** |
| S4 | Provider write/flush faults (transient + permanent) | `test_adversarial_storage_controller` | controller recovers from transient; raising store task **strands visit (G1) + tears down shared connection (G1b)**; **permanent write fault = DEFECT (G2)** |
| S5 | Browser killed mid-visit | `test_adversarial_pipeline` | recovery asserted (CI) |
| S6 | Malformed / hostile records (huge values, injection-y strings, missing visit_id) | `test_adversarial_storage_controller` (SQLite) | **SURVIVES** |

## Confirmed robustness gaps (defects)

These are captured as `xfail(strict=True)` tests — the failing assertion *is*
the finding. When a gap is fixed the test XPASSes and CI flags it, prompting
removal of the marker.

### G1 — A raising `store_record` task strands the visit

`StorageController.store_record` fires each record off as an un-awaited
`asyncio` task and only surfaces exceptions when `finalize_visit_id` awaits
them. If a store task raises:

- on the **finalize** path, the exception propagates out of `finalize_visit_id`
  (after the tasks were already popped) before the completion token is
  recorded, so the visit is **never enqueued to the completion queue**;
- on **shutdown**, the same raise aborts the shutdown finalize loop, so an
  **unfinalized** visit (e.g. browser died mid-visit) is also never enqueued.

Impact: a callback-bearing `CommandSequence` hangs forever, and the visit is
silently lost. Tests: `test_raising_store_record_visit_still_finalizes`,
`test_raising_store_record_unfinalized_visit_enqueued_on_shutdown`.

### G1b — A raising `store_record` task tears down the whole connection

The same raise propagates out of the per-connection handler (`_handler`), which
then closes that connection. Any client still using that **shared** connection
gets a `BrokenPipeError` on its next send. This matters because the
`TaskManager` keeps a single long-lived `DataSocket` (`self.sock`) for
`site_visits` / `crawl_history` / `finalize` records across **all** visits — so
one bad record can break the socket for the rest of the crawl, not just the
offending visit. The controller itself recovers (a good visit on a *fresh*
connection still completes — see `test_transient_store_failure_controller_recovers`),
but the shared connection does not. Test:
`test_raising_store_record_breaks_shared_connection`.

### G2 — A permanent `write_table` fault loses completed visits

A permanent `write_table` failure raises out of `flush_cache` during shutdown,
killing the controller before the completion queue is drained. The visit's
terminal state is lost and the structured-storage shutdown is skipped. Write
failures should be surfaced/counted, not silently drop completed visits. Test:
`test_permanent_write_table_fault_visit_still_completes`.

### G3 — SQLite silently drops unknown-table / unknown-column records

(Pre-existing, tracked in crosslink #28/#30.) `SQLiteStorageProvider.store_record`
catches `OperationalError` for an unknown table or column and only logs
"Unsupported record"; the whole record is dropped with no partial save and no
surfaced count. For a measurement framework this masks data loss as a log line.

The fix for G1/G1b/G2 is a **design call** (where to record the terminal state
when the provider itself is the thing failing — count-and-continue vs.
fail-loud, and whether a per-record failure should ever close the connection)
and should be made by a maintainer; these tests pin the desired invariant.

### Note: the in-memory test provider is not a faithful stand-in for huge values

`MemoryStructuredProvider` round-trips records through a cross-process
`multiprocess.Queue`. A multi-MiB record value deadlocks that queue at shutdown
(the feeder thread blocks on a full pipe that no consumer drains). This is a
**test-harness artifact**, not a pipeline property: the real
`SQLiteStorageProvider` writes the same value to disk without issue
(`test_malformed_records_do_not_break_controller` therefore drives SQLite, not
the memory provider). Keep this in mind when extending the suite.

## Not implemented: S2 (crashing extension modification)

A faithful test of a WebExtension that throws on load / mid-instrumentation /
floods malformed records requires building a deliberately-broken xpi. Shipping
a broken extension build into the repo (or a parallel build pipeline for it) is
out of scope for the test suite and is left as a follow-up. Its **recovery
shape is already covered by S5**: when a broken extension takes the browser down
(or the `BrowserManager` subprocess dies), the BrowserManager restart path is
the same one S5 exercises. The Python side's tolerance of malformed records the
extension might flood is covered by S3/S6.
