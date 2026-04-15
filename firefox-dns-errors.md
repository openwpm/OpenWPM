---
title: "Firefox DNS error strings for WebExtension onErrorOccurred"
tags: ["dns", "firefox"]
sources:
  - url: "https://searchfox.org/mozilla-central/search?q=NS_ERROR_NET_TIMEOUT&path=netwerk/"
    title: ""
    accessed_at: "2026-04-15"
contributors: ["Mp1e"]
created: 2026-04-15
updated: 2026-04-15
---

NS_ERROR_UNKNOWN_HOST is the only DNS-specific error in Firefox. NS_ERROR_NET_TIMEOUT is generic (TCP, TLS, HTTP, WebSocket timeouts). NS_ERROR_DNS_RESOLVE_UNKNOWN_HOST does not exist in Firefox source. DNS timeouts surface as NS_ERROR_UNKNOWN_HOST when the resolver gives up — there is no dedicated DNS timeout error. Source: searchfox.org searches of mozilla-central netwerk/ directory.
