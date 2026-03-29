---
title: "Fix DNS instrument to record all requests in a redirect chain"
tags: [design-doc]
sources: []
contributors: [claude]
created: 2026-03-29
updated: 2026-03-29
---


## Design Specification

### Summary

The DNS instrument currently uses `onCompleted` which fires only after all redirects resolve, silently dropping intermediate DNS lookups. Switching to `onHeadersReceived` fires per-request including every redirect hop, giving researchers a complete picture of DNS resolution across redirect chains. This is a research tool designed for hostile web environments: overcapture is preferable to undercapture.

### Requirements

- REQ-1: `DnsInstrument` must listen on `browser.webRequest.onHeadersReceived` (not `onCompleted`) so that every hop in a redirect chain produces a `dns_responses` row.
- REQ-2: `dnsRecord.used_address` may be `NULL` when `details.ip` is undefined at headers-received time. This is intentional signal (IP not yet resolved), not an error condition.
- REQ-3: The TypeScript TODO comment on `WebRequestOnHeadersReceivedDetails.ip` must be resolved: the field exists in Firefox's WebExtension API but is optional (`ip?: string`); `undefined` maps to `NULL` in the DB by design.
- REQ-4: Every `onHeadersReceived` event fires an independent `browser.dns.resolve()` call for that request's hostname. No deduplication by hostname within a visit — repeated lookups for the same host are valid data (short TTLs, dynamic resolution).
- REQ-5: A test must verify that a 2-hop redirect chain (A→B→C served by the local test server) produces exactly 3 rows in `dns_responses`.
- REQ-6: The existing `test_name_resolution` test must continue to pass, asserting `used_address == "127.0.0.1"` for a non-redirecting request (verifies `ip` field is populated when available).

### Acceptance Criteria

- [ ] AC-1 (REQ-1): `Extension/src/background/dns-instrument.ts` registers on `browser.webRequest.onHeadersReceived` and removes from `onCompleted`. `cleanup()` removes the `onHeadersReceivedListener`.
- [ ] AC-2 (REQ-2, REQ-3): `WebRequestOnHeadersReceivedDetails` interface in `Extension/src/types/browser-web-request-event-details.ts` has the TODO removed and replaced with a comment explaining: `ip` is present in Firefox's `onHeadersReceived` per MDN; may be `undefined` if IP not yet resolved; `NULL` in `dns_responses.used_address` is valid and meaningful.
- [ ] AC-3 (REQ-5): `test/test_dns_instrument.py` contains `test_redirect_chain_dns` that navigates to `server.url("/MAGIC_REDIRECT") + "?dst=" + ...` constructing a 2-hop chain, and asserts `len(results) == 3`.
- [ ] AC-4 (REQ-6): `test_name_resolution` passes unchanged (or updated only for `server: ServerUrls` fixture injection from PR #1136) and still asserts `used_address == "127.0.0.1"`.
- [ ] AC-5 (REQ-4): No deduplication logic exists in `DnsInstrument` — confirmed by code review.

### Architecture

**Modified files:**
- `Extension/src/background/dns-instrument.ts` — swap `onCompleted` → `onHeadersReceived` (PR #1021 already does this). Rename `onCompleteListener` field to `onHeadersReceivedListener` for clarity. The `onCompleteDnsHandler` method name is a minor misnomer but not blocking.
- `Extension/src/types/browser-web-request-event-details.ts` — resolve the `ip?: string` TODO with explanatory comment.
- `test/test_dns_instrument.py` — add `test_redirect_chain_dns`. Uses the existing `MAGIC_REDIRECT` handler in `test/utilities.py` (lines 56–84) which chains 301 redirects via `?dst=` query params. No new test infrastructure needed.

**Data flow (per hop in redirect chain):**
```
onHeadersReceived fires for hop N
  → onCompleteDnsHandler called
    → dnsRecord.used_address = details.ip  (may be undefined → NULL)
    → browser.dns.resolve(hostname)        (async, always fires)
    → saveRecord("dns_responses", dnsRecord)
onHeadersReceived fires for hop N+1
  → same flow, new request_id
```

**Schema:** `dns_responses.used_address TEXT` (nullable) in `openwpm/storage/schema.sql` — no change needed, NULL is already valid.

**Redirect test URL construction** using `MAGIC_REDIRECT`:
```python
# 2-hop chain: /MAGIC_REDIRECT → /MAGIC_REDIRECT → /simple_b.html
chain_url = (
    server.url("/MAGIC_REDIRECT")
    + "?dst=" + server.url("/MAGIC_REDIRECT")
    + "?dst=" + server.url("/test_pages/simple_b.html")
)
```
The test server fires 3 `onHeadersReceived` events (initial + 2 redirects), producing 3 `dns_responses` rows.

### Out of Scope

- Deduplication of DNS records by hostname within a visit
- Recording redirect chain linkage (which request_id redirected to which)
- Changes to `dns_responses` schema
- Any change to `http-instrument.ts` or other instruments
- Handling `onBeforeRedirect` as an alternative event (onHeadersReceived is correct and sufficient)

