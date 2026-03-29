---
title: "OpenTelemetry tracing for command execution and storage"
tags: [design-doc]
sources: []
contributors: [claude]
created: 2026-03-29
updated: 2026-03-29
---


## Design Specification

### Summary

Add opt-in OpenTelemetry tracing to OpenWPM for developer observability — understanding where crawl time is spent and whether the async storage pipeline (especially S3 batch saving with futures-returning-futures) is behaving correctly. Activated exclusively via `OTEL_EXPORTER_OTLP_ENDPOINT` env var; no-op and zero user-visible impact when the var is absent. This is a developer/ops tool and will not be user-facing documentation.

### Requirements

- REQ-1: OTel tracing must be a strict no-op (no overhead, no errors) when `OTEL_EXPORTER_OTLP_ENDPOINT` is not set. The default OTel no-op tracer satisfies this.
- REQ-2: Each `CommandSequence` execution in `BrowserManagerHandle` must be wrapped in a root span with the visit URL and browser ID as attributes.
- REQ-3: Each individual command within a sequence must be wrapped in a child span named after the command class, with timeout as an attribute.
- REQ-4: Browser startup (`deploy_firefox`, extension load) must be wrapped in a span to measure cold-start cost per browser restart.
- REQ-5: `StorageController`'s async batch save pipeline must be instrumented with spans covering: (a) the point a record is enqueued, (b) the point a `finalize_visit_id` future is created, (c) the point the future resolves. This is the highest-value instrumentation — the futures-returning-futures pattern for S3 is complex and correctness is uncertain.
- REQ-6: OTel SDK must be configured per child process via `configure_otel_for_process()` called after each fork, because the SDK's background exporter thread does not survive `fork()`.
- REQ-7: OTel deps (`opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`) must be added to `environment.yaml` under pip dependencies, consistent with the existing pip block format.
- REQ-8: Provider shutdown must be called in `TaskManager.close()` and in `Process.run()` cleanup to flush spans before process exit.

### Acceptance Criteria

- [ ] AC-1 (REQ-1): Running `demo.py --headless` with `OTEL_EXPORTER_OTLP_ENDPOINT` unset produces no errors, no OTel-related log output, and no performance regression.
- [ ] AC-2 (REQ-2, REQ-3): With a live OTLP endpoint, a crawl of a single URL produces a root span `execute_command_sequence` with child spans for each command (e.g. `GetCommand`, `FinalizeCommand`).
- [ ] AC-3 (REQ-4): A span `browser_startup` appears as a child of the first `execute_command_sequence` span (or as a sibling root span) and covers the full Firefox launch duration.
- [ ] AC-4 (REQ-5): With S3 storage, spans appear for enqueue, `finalize_visit_id` future creation, and future resolution, allowing async pipeline depth to be measured from a trace.
- [ ] AC-5 (REQ-6): `configure_otel_for_process(service_name)` exists in `openwpm/utilities/multiprocess_utils.py`, is called in `Process.run()` before `run_impl()`, and is called in `TaskManager.__init__` after browser processes are launched.
- [ ] AC-6 (REQ-7): `environment.yaml` pip block contains `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http` at pinned versions. `conda env create` succeeds from scratch.
- [ ] AC-7 (REQ-8): `provider.shutdown()` is called in `TaskManager.close()` and in `Process.run()` finally block. No spans are lost on normal crawl completion.

### Architecture

**Files changed:**
- `environment.yaml` — add three OTel pip deps (pinned versions matching otel branch: `1.30.0`)
- `openwpm/utilities/multiprocess_utils.py` — add `configure_otel_for_process(service_name: str)`: no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` unset, otherwise creates `TracerProvider` with `Resource(service.name)` and `BatchSpanProcessor(OTLPSpanExporter())`. Call in `Process.run()` before `run_impl()`, with `provider.shutdown()` in finally.
- `openwpm/task_manager.py` — acquire module-level `_tracer = trace.get_tracer(__name__)`. Call `configure_otel_for_process("openwpm-task-manager")` in `__init__` after all browser processes launched. Call `provider.shutdown()` in `close()`.
- `openwpm/browser_manager.py` — wrap `_run_command_sequence()` with `@_tracer.start_as_current_span("execute_command_sequence")`, set `visit_id`/`browser_id` attributes. Wrap each command dispatch with `with _tracer.start_as_current_span(type(command).__name__)`. Wrap browser startup with `with _tracer.start_as_current_span("browser_startup")`.
- `openwpm/storage/storage_controller.py` — add spans for: record enqueue (lightweight, high-frequency), `finalize_visit_id` call (captures when the flush token is issued), and future resolution callback (captures when S3 batch actually completes). When instrumentation is absent these are no-ops.

**Fork safety:** OTel's `BatchSpanProcessor` runs a background thread. After `fork()`, that thread does not exist in the child. `configure_otel_for_process()` must be called in each child after the fork, creating a fresh `TracerProvider`. The parent's provider is separate and continues independently.

**Span hierarchy (per browser, per visit):**
```
execute_command_sequence [browser_id, visit_id, url]
  ├── GetCommand [timeout]
  │     └── storage: enqueue_record (×N rows)
  ├── FinalizeCommand
  │     └── storage: finalize_visit_id
  │           └── storage: future_resolved [table_counts, duration_ms]
  └── post_cs_chores
```

**No user-facing configuration.** The only knob is `OTEL_EXPORTER_OTLP_ENDPOINT`. No `ManagerParams` field. No documentation addition.

### Out of Scope

- Metrics (counters, gauges, histograms) — tracing only
- Log correlation (OTel logs bridge)
- `ManagerParams.otel_endpoint` or any user-facing config
- Test coverage requiring a live OTLP endpoint or test container
- Replacing `MPLogger` with OTel logging
- Any WebSocket or StorageController threading changes

