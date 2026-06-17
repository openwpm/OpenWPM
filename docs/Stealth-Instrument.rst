Stealth JavaScript Instrument
=============================

The **stealth** JavaScript instrument is an alternative to the legacy
``js_instrument`` for recording how a page uses Web APIs (canvas, ``navigator``,
storage, and so on). It captures the same kind of per-call data, but is built so
that a page has a much harder time noticing that it is being instrumented, and a
much harder time tampering with the records OpenWPM collects.

This page explains how to turn it on, why you might prefer it over the legacy
instrument, and how to customise what it captures. For the design rationale and
internals, see the developer reference
:doc:`developers/Stealth-Instrumentation`.

Why use the stealth instrument
-------------------------------

The stealth instrument is the result of research into how reliably OpenWPM can
measure hostile or evasive pages [Krumnow2022]_. It offers two user-facing
advantages over the legacy ``js_instrument``:

- **Much harder to detect.** A page can fingerprint the legacy instrument and
  change its behaviour (or refuse to run) when it notices it is being measured.
  The stealth instrument leaves essentially no page-observable trace, so pages
  that try to evade instrumentation are far less likely to succeed. This matters
  for measurement quality: a page that detects the crawler can silently skew your
  dataset.

- **More robust data delivery.** The legacy instrument hands its records to
  OpenWPM over a channel that a hostile page can reach into — letting the page
  drop your records, or even forge fake ones. The stealth instrument delivers its
  records over a channel the page cannot touch, so the data you collect is much
  harder for a page to suppress or poison.

In exchange for these properties the stealth instrument has some capture
differences from the legacy instrument; those trade-offs are documented in the
developer reference. If you do not need stealthiness, the legacy
``js_instrument`` remains available and unchanged.

Enabling the stealth instrument
-------------------------------

The stealth instrument is controlled by the ``stealth_js_instrument`` flag on
``BrowserParams``:

.. code-block:: python

   browser_params.stealth_js_instrument = True

The stealth instrument and the legacy ``js_instrument`` are **mutually
exclusive** — they cannot both be enabled on the same browser. Enabling both
raises a ``ConfigError`` when the configuration is validated, so pick one:

.. code-block:: python

   # Use the stealth instrument instead of the legacy one
   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False  # leave the legacy instrument off

Customising what gets instrumented
----------------------------------

By default — that is, when you only set the flag — the stealth instrument
captures a sensible built-in set of fingerprinting-relevant APIs, so it works
out of the box with no further configuration.

To control exactly which APIs and properties are recorded, provide your own list
of settings via ``stealth_js_instrument_settings`` on ``BrowserParams``:

.. code-block:: python

   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False
   browser_params.stealth_js_instrument_settings = [
       {
           "object": "CanvasRenderingContext2D",
           "instrumentedName": "CanvasRenderingContext2D",
           "logSettings": {
               # which kinds of access to record (method calls, property
               # reads/writes, etc.) for this object
           },
       },
       # ... more entries ...
   ]

When ``stealth_js_instrument_settings`` is left unset, the instrument falls back
to its bundled default surface, so you only need to supply this field if you want
to instrument a different set of APIs than the default.

The shape of a settings entry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each entry in the list describes one Web API object to instrument:

- ``object`` — the **bare global name** of the API to instrument, looked up
  directly in the page's global scope. Use names such as
  ``"CanvasRenderingContext2D"``, ``"Navigator"``, ``"Storage"``, or
  ``"document"``. (This is *not* the same format as the legacy
  ``js_instrument_settings``, which uses a dotted ``window['...']`` path. Stealth
  settings are written in the stealth shape directly.)
- ``instrumentedName`` — the name this object is recorded under in the collected
  data.
- ``logSettings`` — what to record for that object: which methods and properties
  to capture and which kinds of access (calls, reads, writes) to log.

Prototype-level instrumentation
-------------------------------

The stealth instrument hooks each Web API at the **prototype level rather than on
individual objects**. In practice this means it captures use of an API no matter
which specific object the page happens to call it on: every canvas context, every
``navigator`` access, every storage object shares the same underlying definition,
and instrumenting that shared definition once covers all of them. You therefore
do not need to know in advance which objects a page will create — the
instrumentation is in place for all of them.

.. [Krumnow2022] Krumnow, Jonker & Karsch, *"Analysing and strengthening
   OpenWPM's reliability"*, arXiv:2205.08890, 2022.
   https://arxiv.org/abs/2205.08890
