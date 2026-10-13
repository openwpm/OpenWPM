Stealth and legacy JS instruments
=================================

OpenWPM has two JavaScript instruments, **legacy** (``js_instrument``) and
**stealth** (``stealth_js_instrument``); enabling both raises a ``ConfigError``.
This page covers how they relate and why legacy is kept. The stealth mechanism
is in :doc:`Stealth-Instrumentation`, its requirements and tests in
:doc:`Stealth-Requirements`.

Where each instrument runs
--------------------------

Legacy injects its wrappers into the page world from a content script. Stealth
runs in a privileged sandbox per window global, started by a window actor, and
reaches the page through `Xray vision
<https://firefox-source-docs.mozilla.org/dom/scriptSecurity/xray_vision.html>`_,
exposing only what it chooses via `exportFunction
<https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Sharing_objects_with_page_scripts>`_.
Two Xray properties are load-bearing: a script holding an Xray sees the native
object rather than any page redefinition, and properties the instrument adds on
its side are expandos the page cannot observe.

Two independent axes
--------------------

Stealth improves on legacy on both axes of the threat model
(:ref:`stealth-threat-model`). **Detectability**: every artifact the reliability
paper names (:ref:`legacy-detectability`) is absent under stealth; what it does
leave is under :ref:`stealth-residual-tells`. **Tamper-resilience**: legacy
ships records over a DOM ``dispatchEvent``, stealth over the process message
manager, which has no page-reachable handle (:ref:`stealth-disruptability`).

.. _stealth-what-changes:

What changes when you switch
----------------------------

Legacy is a narrow, opt-in capture fallback, not a co-equal peer. Two
capabilities have no stealth equivalent:

1. **Recursion into plain objects.** Stealth never recurses. The gap is
   exactly recursion into plain containers: most recursively reached nodes are
   platform-typed (``Navigator``, ``Screen``, audio interfaces) and the
   settings migrator (:ref:`stealth-migrator`) translates them; only bare
   ``Object``/``Array`` nodes (e.g. ``navigator.languages``) cannot be hooked.
   The migrator reports every legacy member a translation does not cover,
   plain-object nodes and ``navigator.sendBeacon`` among them, and exits
   non-zero, which is how a study learns whether it depends on this gap.
2. **Recorded arguments and values.** Legacy serializes in the page, running
   getters, ``toJSON`` and ``Proxy`` traps, so it records the store contents
   on ``window.localStorage``/``sessionStorage`` gets, the fields of host
   objects with a ``toJSON`` (e.g. the SDP of
   ``RTCPeerConnection.localDescription``, `#1246
   <https://github.com/openwpm/OpenWPM/issues/1246>`_), nested functions as
   ``"FUNCTION"`` and a ``Date`` as an ISO string. Stealth runs no page code
   while recording and keeps less ("Recorded values" under
   :ref:`stealth-residual-tells`).

A study reaches for legacy only by accepting its detectability and its
page-reachable channel in exchange for one of these. Mutual exclusion keeps them
available at no cost to a stealth run; the cost is maintaining code most
studies do not use. Legacy stays until both gaps are closed in stealth or shown
to be unused.

The bundled default (``Extension/src/stealth/settings.ts``) is a curated,
stealth-shaped configuration, not a copy of legacy's
``collection_fingerprinting`` preset. Both write the ``javascript`` table with
the same columns, and a captured call yields the row legacy would, ``symbol``
included once mapped through ``db_utils.legacy_symbol`` (`Shared-prototype
members`_). Published analyses query ``symbol`` by exact equality
(``WHERE symbol='window.navigator.userAgent'``), so the default's
``instrumentedName`` for the ``Navigator``, ``Screen`` and ``document``
entries is ``window.navigator``, ``window.screen`` and ``window.document``
(what ``clean_js_instrumentation_settings`` derives from
``collection_fingerprinting``). ``TestStealthSymbolParity``
(``test/test_stealth.py``) runs one probe page through both instruments and
requires every legacy ``symbol`` among the mapped stealth ones.

- **Captured identically:** RTCPeerConnection, HTMLCanvasElement,
  CanvasRenderingContext2D, Storage (``getItem``/``setItem``/…),
  ``window.navigator.*`` (``userAgent``, ``platform``, ``languages``,
  ``webdriver``, …), ``window.screen.*`` (``colorDepth``, ``pixelDepth``),
  ``window.document.cookie``, ``window.document.referrer``, ``window.name``
  (get/set), ``window.localStorage`` / ``window.sessionStorage`` (property
  get), and the own properties of the audio node/context children (e.g.
  ``AnalyserNode.frequencyBinCount``, ``AnalyserNode.getFloatFrequencyData``,
  ``AudioContext.close``).
- **Additionally by stealth:** ``AudioWorkletNode`` (the modern replacement
  legacy lacks); all ``Screen`` properties (legacy: only
  ``colorDepth``/``pixelDepth``); the ``receiver`` column, the interface of the
  object each call, get or set was made on (:ref:`stealth-receiver`), which
  legacy leaves NULL.
- **By legacy only:** ``window.navigator.sendBeacon``, left to
  ``http_instrument`` (:ref:`stealth-send-beacon`).
- **Re-entrant calls.** Recording runs no page code, so a call the page makes
  while another instrumented call is in progress (from a getter the native
  reads, or an argument's ``toString``) is recorded; legacy's re-entrancy guard
  drops it.

Recorded values, failed sets and the ``top_level_url`` of navigated-away
documents differ too (:ref:`stealth-residual-tells`), as does frame coverage
(:ref:`frame attribution <stealth-frame-attribution>`).

Shared-prototype members
~~~~~~~~~~~~~~~~~~~~~~~~

A member several interfaces inherit from one prototype
(``AudioNode.connect``/``disconnect``,
``BaseAudioContext.createGain``/``createOscillator``/``sampleRate``/…) is
hooked once, on that prototype: redefining the same native under several child
names would be page-observable. Legacy copied it onto each child it listed. So
``symbol`` names the owner (``AudioNode.connect``,
``[AudioContext|OfflineAudioContext].createGain``) where legacy named the
child (``GainNode.connect``), and ``receiver`` holds the child's interface.
``db_utils.legacy_symbol`` combines the two into legacy's ``symbol``:

.. code-block:: python

   from openwpm.utilities.db_utils import legacy_symbol

   legacy_symbol("AudioNode.connect", "GainNode")  # "GainNode.connect"
   legacy_symbol("window.document.cookie", "HTMLDocument")  # unchanged

Legacy rows and instance paths are returned unchanged, so it applies to a mixed
dataset. Stealth also records shared members on node types legacy never listed
(``DynamicsCompressorNode.connect``), so the mapped symbols are a superset of
legacy's; ``TestStealthSymbolParity`` requires each extra to be such a
receiver-attributed member. For a config translated by the migrator, a member
legacy reached through an instance path (``window.document.addEventListener``)
maps to its receiver's interface (``HTMLDocument.addEventListener``): one
interface can be reached through several paths, so a row does not determine
the path.

Why the instruments stay mutually exclusive
-------------------------------------------

Allowing both, with an error only when a property is claimed by both, would let
a study run stealth for most APIs and legacy for the rest. That yields a stealthy
browser only if legacy's detectability is confined to the properties it wraps,
and it is not. Legacy is detectable whatever it instruments (issue
`#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_):

- ``Object.getPropertyDescriptor`` and ``Object.getPropertyNames`` are assigned
  onto the page's ``Object`` before any settings are read and never removed
  (``Extension/src/lib/js-instruments.ts``). Neither exists in a real browser,
  so one ``typeof`` check identifies OpenWPM even with an empty configuration.
  PR `#1191 <https://github.com/openwpm/OpenWPM/pull/1191>`_ removes them.
- A ``<script>`` element carrying ``data-event-id`` and ``data-testing`` is
  injected as the first child of ``<html>`` at ``document_start`` and removed.
  Randomising the event id hides the value, not the structure, and a page
  ``MutationObserver`` registered earlier sees the insertion.
- The page-scope and content-scope halves communicate over a ``CustomEvent`` on
  ``document``; a page that patches ``dispatchEvent``/``addEventListener``
  first observes that traffic.

Each follows from executing in the page's principal, not from a particular
wrapper. Removing them means moving execution into an isolated world, which is
what stealth is: hence a separate instrument rather than a hardening pass over
legacy.

.. _legacy-ceiling:

Legacy's detectability ceiling is architectural
-----------------------------------------------

Most of legacy's tells yield to ordinary engineering. Wrapper arity and name can
be copied from the native at no capture cost (PR `#1210
<https://github.com/openwpm/OpenWPM/pull/1210>`_). Prototype pollution is an
implementation choice: hooking each inherited member once on its owning
prototype and attributing by ``this`` removes it, at a data-layout cost
(:ref:`legacy-detectability`). Frame coverage is more cases, each coverable.

What does not go away is the position. A page-world wrapper can patch only its
own realm's ``Function.prototype.toString``, so the unpatched intrinsic is
always one fresh realm away:
``iframe.contentWindow.Function.prototype.toString.call(fn)`` returns the
wrapper body. Keeping up means re-instrumenting every realm as it is created, a
race the instrument stays hidden in only as long as it arrives first.

Stealth is out of the race: from its sandbox it reads page objects through Xrays
and exposes only what it chooses through ``exportFunction``, so it never mutates
a page intrinsic, and its window actor instruments every window global when it
is created, before the page can reach it. Because Gecko reports every new window
global, no DOM API (``appendChild``, ``innerHTML``, ``document.write``,
``contentWindow``, ...) is hooked to catch new frames (the ``D10-fp-*`` rows in
:doc:`Stealth-Requirements`).

This covers the vectors the reliability paper names (``toString``, prototype
pollution, arity, name), not every conceivable tell; of those, only the
realm-local ``toString`` patch is structural to a page-world wrapper.

Open work
---------

- **Legacy footprint:** whether legacy's detectability can be confined to its
  wrapped APIs (`#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_);
  until then the instruments stay mutually exclusive.
- **Overlap validation:** relax mutual exclusion to an error only for a property
  claimed by both instruments, once the footprint allows it.
- **Shared base:** extract webdriver hiding and native ``toString``/arity from
  stealth so a legacy run stops failing the easy checks at no capture cost.
- **Legacy record channel:** move legacy's delivery off the DOM (e.g.
  ``browser.runtime`` from the content script), so a detectable legacy run is
  not also disruptable; tamper-resilience is a channel property and can be
  added to legacy without making it undetectable.
