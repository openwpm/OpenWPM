---
title: "Exclude DNS errors from consecutive failure limit"
tags: [design-doc]
sources: []
contributors: [claude]
created: 2026-03-29
updated: 2026-03-29
---


## Design Specification

### Summary

DNS resolution failures (`dnsNotFound`) are routine noise when crawling large domain lists like Tranco and do not indicate corrupt crawler state. Unlike real failures (crashes, timeouts, JS errors), a DNS miss means the domain simply doesn't exist — the browser and instrumentation are functioning correctly. This change excludes `dnsNotFound` errors from the `failure_count` that drives `TaskManager`'s abort threshold, preventing large crawls from terminating prematurely.

### Requirements

- REQ-1: When a command results in `command_status == "neterror"` and `error_text == "dnsNotFound"`, `task_manager.failure_count` must NOT be incremented in `openwpm/browser_manager.py`.
- REQ-2: DNS errors must still be recorded in `crawl_history` with `command_status="neterror"` and `error="dnsNotFound"` — the record is kept, only the failure counter is skipped.
- REQ-3: DNS errors still set `self.restart_required = True` — the browser restarts after a DNS error as it would for any non-OK command. Only the failure counter is exempted.
- REQ-4: The exemption is limited strictly to `error_text == "dnsNotFound"`. Other neterror types (`connectionRefused`, `netOffline`, etc.) continue to count against `failure_limit` as before.
- REQ-5: The behavior is not configurable — DNS errors are always excluded from failure counting. Users who want different behavior should file a feature request.

### Acceptance Criteria

- [ ] AC-1 (REQ-1): In `browser_manager.py`, the `failure_count += 1` block (currently at line 466) is gated on `not is_dns_error` where `is_dns_error = (command_status == "neterror" and error_text == "dnsNotFound")`.
- [ ] AC-2 (REQ-2): The existing test `test_parse_neterror_integration` in `test/test_webdriver_utils.py` passes: navigating to `http://website.invalid` produces a `crawl_history` row with `command_status="neterror"` and `error="dnsNotFound"`.
- [ ] AC-3 (REQ-3): `self.restart_required` is still set to `True` for DNS errors (the `is_dns_error` exemption only wraps the `failure_count` block, not the `restart_required` assignment).
- [ ] AC-4 (REQ-4): A test navigating to 100+ non-existent domains in sequence completes without raising `CommandExecutionError`, even when `ManagerParams.failure_limit` is set below 100. (Validates REQ-1 at scale.)
- [ ] AC-5 (REQ-4): Non-DNS neterrors (e.g. `connectionRefused`) still increment `failure_count` — confirmed by unit test for `is_dns_error` returning `False` for other error types.

### Architecture

Single file changed: `openwpm/browser_manager.py`.

The relevant block in `BrowserManagerHandle._run_command_sequence()` (lines 464–481 on master):

```python
if command_status != "ok":
    with task_manager.threadlock:
        task_manager.failure_count += 1          # ← guarded by is_dns_error check
    if task_manager.failure_count > task_manager.failure_limit:
        ...
        return
    self.restart_required = True                  # ← NOT guarded; browser still restarts
```

The `is_dns_error` predicate:
```python
is_dns_error = (
    command_status == "neterror"
    and error_text is not None
    and error_text == "dnsNotFound"
)
```

`error_text` is populated from `parse_neterror()` in `openwpm/commands/utils/webdriver_utils.py`, which extracts the error code from Firefox's `about:neterror` URL. `dnsNotFound` is the specific code for DNS resolution failure.

The `crawl_history` store (lines 439–455) runs unconditionally before the failure check, so DNS errors are always recorded regardless of the exemption.

**Test infrastructure:** `test/test_webdriver_utils.py` already has `test_parse_neterror_integration` which navigates to `http://website.invalid` and checks the `crawl_history` row. The new scale test can reuse the `task_manager_creator` fixture and a list of fabricated non-existent hostnames.

### Out of Scope

- Configurable DNS error behavior (not needed; hardcoded exemption is correct for OpenWPM's use case)
- Exempting other neterror types (only `dnsNotFound` is in scope)
- Changes to `crawl_history` schema or storage
- Retry logic for DNS errors
- Any changes to `ManagerParams` or `BrowserParams`

