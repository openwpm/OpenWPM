Stealth JavaScript Instrument
=============================

The **stealth** JavaScript instrument is an alternative to the legacy
``js_instrument`` for recording how a page uses Web APIs (canvas, navigator,
storage, and so on). It captures the same kind of per-call data, delivers it
over a channel the page cannot reach, and is built so that a page observes the
same values it would observe in an uninstrumented Firefox.

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
  The stealth instrument is tested differentially: a probe page records what it
  can observe about the instrumented APIs (function source, arity, name,
  constructibility, ``constructor`` identity, thrown errors, which builtins the
  instrument calls, getters it triggers, cross-realm views) and must record
  identical values with and without the instrument. The tells that remain are
  listed under "Known residual tells" in the developer reference, along with
  what is not recorded: workers. This matters
  for measurement quality: a page that detects the crawler can silently skew
  your dataset.

- **Tamper-resistant data delivery.** The legacy instrument hands its records
  to OpenWPM over a channel a hostile page can reach into, letting the page drop
  your records or forge fake ones. The stealth instrument delivers its records
  over a channel outside the page's reach, so a page can neither drop records in
  transit nor inject fake ones. A page can still stop a specific property from
  being recorded by deleting or redefining it, exactly as under legacy; the
  developer reference explains why that gap is left open.

In exchange for these properties the stealth instrument has some capture
differences from the legacy instrument; :doc:`developers/Stealth-and-Legacy-JS-Instruments`
lists them and explains when legacy is still the right choice. If you do not need stealthiness, the legacy
``js_instrument`` remains available and unchanged.

Enabling the stealth instrument
-------------------------------

The stealth instrument is controlled by the ``stealth_js_instrument`` flag on
``BrowserParams``:

.. code-block:: python

   browser_params.stealth_js_instrument = True

The stealth instrument and the legacy ``js_instrument`` are **mutually
exclusive**: they cannot both be enabled on the same browser. Enabling both
raises a ``ConfigError`` when the configuration is validated, so pick one:

.. code-block:: python

   # Use the stealth instrument instead of the legacy one
   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False  # leave the legacy instrument off

Customising what gets instrumented
----------------------------------

Setting only the flag gives you a built-in set of fingerprinting-relevant APIs,
so the instrument works out of the box with no further configuration.

That default covers the legacy instrument's ``collection_fingerprinting`` set
except ``navigator.sendBeacon`` (see below), and adds ``AudioWorkletNode``, which
legacy does not instrument. Members the audio
interfaces inherit from a shared parent are recorded once under the parent
(``AudioNode.connect`` rather than ``GainNode.connect``). In the settings the
names differ in form only: where legacy writes ``window.navigator``,
``window.screen`` and ``window.document``, the stealth default names
``Navigator``, ``Screen`` and ``document``.

To control exactly which APIs and properties are recorded, provide your own list
of settings via ``stealth_js_instrument_settings`` on ``BrowserParams``:

.. code-block:: python

   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False
   browser_params.stealth_js_instrument_settings = [
       {
           "object": "HTMLCanvasElement",
           "instrumentedName": "HTMLCanvasElement",
           "depth": 0,
           "logSettings": {
               "propertiesToInstrument": ["toDataURL", "getContext"],
               "nonExistingPropertiesToInstrument": [],
               "excludedProperties": [],
               "overwrittenProperties": [],
               "logCallStack": False,
               "logFunctionsAsStrings": False,
               "logFunctionGets": False,
               "preventSets": False,
               "recursive": False,
               "depth": 5,
           },
       },
       # ... more entries ...
   ]

When ``stealth_js_instrument_settings`` is left unset (``None``), the instrument
falls back to its bundled default surface, so you only need to supply this field
if you want to instrument a different set of APIs than the default. An empty
list instruments nothing.

The default leaves ``navigator.sendBeacon`` unwrapped: wrapping it drops
beacons a page sends from ``pagehide`` while its process shuts down, which the
site can notice. Instead, enable ``http_instrument`` to record the beacon
request including its body, and ``callstack_instrument``, once #1178 restores
it, for its JavaScript origin; to wrap it anyway, list ``sendBeacon`` in a custom surface and accept
the loss. See the developer reference.

Several entries may resolve to the same prototype; each member is instrumented
once, under the first entry that lists it.

The shape of a settings entry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each entry in the list describes one Web API object to instrument:

- ``object`` (required): the **bare global name** of the API to instrument,
  looked up directly in the page's global scope. This is usually an *interface*,
  MDN's term for the named type whose prototype the page's objects share:
  ``"CanvasRenderingContext2D"``, ``"Navigator"``, ``"Storage"``. It can also be
  a global object rather than an interface, which is why ``"document"`` and
  ``"window"`` are lowercase: they name single objects that already exist, not
  types that instances are built from. (This is *not* the same format as the
  legacy ``js_instrument_settings``, which uses a dotted ``window['...']`` path.
  Stealth settings are written in the stealth shape directly.)
- ``instrumentedName`` (required): the name this object is recorded under in the
  collected data. It is not inferred from ``object``; the schema rejects an entry
  without it.
- ``logSettings`` (required): what to record for that object, i.e. which methods and
  properties to capture and which kinds of access (calls, reads, writes) to log.

Known limitations
-----------------

The stealth instrument hooks each Web API at the **prototype level rather than on
individual objects**. That is what makes it thorough: every canvas context, every
navigator access and every storage object shares the same underlying definition,
so instrumenting that definition once covers all of them, and you do not need to
know in advance which objects a page will create.

The cost is in attribution. When several interfaces inherit a method from a
shared ancestor, the hook sits on the ancestor that owns it, so the call is not
filed under the leaf interface the page happened to reach it through. The
``receiver`` column narrows this back down: it records the interface of the
object the call was actually made on, which is the most specific interface
available at call time. What is lost is not the call, and not the object's
interface, but the path by which the page arrived at the member.

.. [Krumnow2022] Krumnow, Jonker & Karsch, *"Analysing and strengthening
   OpenWPM's reliability"*, `arXiv:2205.08890
   <https://arxiv.org/abs/2205.08890>`_, 2022.
