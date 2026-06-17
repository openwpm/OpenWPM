Stealth and legacy JS instruments
=================================

OpenWPM has two JavaScript instruments: the **legacy** instrument
(``js_instrument``) and the **stealth** instrument (``stealth_js_instrument``).
They are mutually exclusive: enabling both raises a ``ConfigError``. This page
explains how the two relate, why legacy is kept although stealth supersedes it,
and what each records differently. The stealth mechanism itself is described in
:doc:`Stealth-Instrumentation`; its requirements and tests in
:doc:`Stealth-Requirements`.

Where each instrument runs
--------------------------

The difference between the two turns on Gecko's script-security model. Legacy
injects its wrappers into the page world, from a content script. Stealth runs
in a privileged sandbox per window global, started by a window actor, and
reaches the page through `Xray vision
<https://firefox-source-docs.mozilla.org/dom/scriptSecurity/xray_vision.html>`_,
exposing only what it chooses to via `exportFunction
<https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Sharing_objects_with_page_scripts>`_.
Two Xray properties are load-bearing: a script holding an Xray sees the native
object rather than any page redefinition, and properties the instrument adds on
its side are expandos the page cannot observe.

Two independent axes
--------------------

Stealth improves on legacy along two axes. They are separate mechanisms with
separate root causes; neither follows from the other.

- **Detectability** is a property of the instrument's **footprint**: what it
  leaves visible in the page. Every artifact the reliability paper (Krumnow,
  Jonker & Karsch, `arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_,
  2022) names is absent under stealth: ``toString`` returning the wrapper body
  (stealth's ``exportFunction`` forwarders print the native source string from
  every realm), mismatched arity (the forwarders declare the native's parameter
  count), prototype pollution (only the instrumented members are redefined, on
  the object where Firefox defines them, so own keys and descriptor shapes
  match), leaked globals (``window.jsInstruments``, ``getInstrumentJS``) and
  ``navigator.webdriver`` (overridden to ``false``). What stealth does leave is
  listed under "Known residual tells" in :doc:`Stealth-Instrumentation`.
- **Tamper-resilience** is a property of the **record channel**. The paper's two
  tamper threats, **disruption** (suppressing record delivery) and
  **false-data** (forging records), need a page-reachable channel. Legacy ships
  records over a DOM ``dispatchEvent``; stealth sends them over the process
  message manager, which has no page-reachable handle. This holds independently
  of detectability: an undetectable instrument on the DOM channel would still
  be disruptable, and a detectable one on an off-DOM channel would not be.

On raw wrapper-deletability the two are equal: both install wrappers with the
native ``configurable: true``, so a page can ``delete`` or redefine a wrapped
property under either and stop it being recorded. Stealth's advantage is the
channel, not the wrapper; why the wrapper is left deletable is explained in
:ref:`stealth-disruptability`.

Legacy is therefore both more detectable and more disruptable, and stealth
addresses each on its own terms.

Why legacy is kept
------------------

Legacy is a narrow, opt-in capture fallback, not a co-equal peer. Two
capabilities have no stealth equivalent, and they are the reason it stays:

1. **Recursion into plain objects.** Capturing the ``Object``/``Array``
   instances an instrumented getter returns means defining accessors on those
   page instances, since they have no global interface prototype to hook: a
   page-observable own-property mutation. Stealth refuses to do that and
   rejects ``logSettings.recursive`` at config validation with a
   ``ConfigError``. The gap is exactly "recursion into plain containers": most
   recursively reached nodes are platform-typed (``Navigator``, ``Screen``,
   audio interfaces) and the settings migrator translates them; only bare
   ``Object``/``Array`` nodes (e.g. ``navigator.languages``) cannot be hooked.
2. **Interface naming of inherited members.** Legacy's descent copies an
   inherited member onto the first prototype in the chain, so a call is filed
   under the interface the member was reached through. Stealth hooks the member
   once, on the prototype that owns it (the only place it stays native), and
   records the receiver's interface in the ``receiver`` column. Every call is
   recorded under either instrument; what differs is the interface name it is
   filed under. Both instruments hook the same objects otherwise: legacy
   resolves ``window['X'].prototype`` (``openwpm/js_instrumentation.py``) and
   defines there (``Extension/src/lib/js-instruments.ts``), and neither records
   the receiving object itself (legacy's ``logCall`` never serializes
   ``this``).

A study reaches for legacy only by accepting both of its shortcomings,
detectability and a page-reachable channel, in exchange for one of these two
capabilities. Keeping legacy behind mutual exclusion preserves them at no cost
to a stealth run; the cost is maintaining code most studies do not use. Legacy
stays until both gaps are closed in stealth or shown to be unused.

What each records differently
-----------------------------

Both write to the ``javascript`` table with the same columns, and for the
default surfaces the ``symbol`` values are identical (``TestStealthSymbolParity``),
so analyses that query ``symbol`` work on data from either. The differences:

- **Surface.** The stealth default covers legacy's
  ``collection_fingerprinting`` set except ``navigator.sendBeacon``, and adds
  ``AudioWorkletNode`` and every ``Screen`` property. ``sendBeacon`` is left
  unwrapped because wrapping it loses beacons a page sends from ``pagehide``
  while its process shuts down; beacons are left to ``http_instrument`` (see
  "Configuring the instrumented surface" in :doc:`Stealth-Instrumentation`).
- **Shared audio methods.** Methods on a shared parent prototype
  (``AudioNode.connect``, ``BaseAudioContext.createGain``, ...) are recorded once
  under the parent by stealth and once per child interface by legacy.
- **Recorded values.** Legacy serializes arguments and values in the page,
  running getters, ``toJSON`` and ``Proxy`` traps. Stealth runs no page code: it
  copies plain objects, arrays and typed arrays from their own data properties
  (128 values and 16 levels across a call's object arguments, 65 536
  characters per string) and records every other object by its brand
  (``[object Storage]``, ``[object Date]``), a ``Proxy`` as ``[object Proxy]``,
  because reading a host object's named properties can change its state.
  Inside a copied object, function-, accessor- and ``Proxy``-valued entries and
  keys named after ``Object.prototype`` members are left out ("Recorded
  values" in :doc:`Stealth-Instrumentation`).
- **Failed sets.** Assigning to a getter-only property records nothing under
  stealth and a ``set(failed)`` row under legacy.
- **Re-entrant calls.** A call a page makes while another instrumented call is
  in progress (from a getter the native reads, or an argument's ``toString``)
  is recorded by stealth; legacy's re-entrancy guard drops it.
- **Frames.** Stealth instruments every window global when it is created, so it
  records calls in a frame's or popup's initial ``about:blank`` document and in
  ``blob:``, ``data:`` and sandboxed documents, none of which legacy records.
- **Attribution.** A stealth record carries the ``document_url`` and
  ``frame_id`` of the document it runs in. The parent authenticates it by the
  window global it comes from and remembers that window's tab and frame, so a
  member called after its window is removed, navigated away (across processes
  too) or closed is recorded under that window's last URL and original tab,
  with the tab's current ``top_level_url``. A record whose tab has closed is
  kept with no tab.
- **Recursion.** Only legacy honours ``logSettings.recursive``; every other
  ``logSettings`` field behaves the same under both.

Why the instruments stay mutually exclusive
-------------------------------------------

Allowing both in one browser, with an error only when a property is claimed by
both, would let a study run stealth for most APIs and legacy for the rest. That
only yields a stealthy browser if legacy's detectability is confined to the
properties it wraps, and it is not. Legacy is detectable whatever it
instruments (issue `#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_):

- ``Object.getPropertyDescriptor`` and ``Object.getPropertyNames`` are assigned
  onto the page's ``Object`` before any settings are read and never removed
  (``Extension/src/lib/js-instruments.ts``). Neither exists in a real browser,
  so one ``typeof`` check identifies OpenWPM even with an empty configuration.
  PR `#1191 <https://github.com/openwpm/OpenWPM/pull/1191>`_ removes them.
- The instrument injects a ``<script>`` element carrying ``data-event-id`` and
  ``data-testing`` as the first child of ``<html>`` at ``document_start`` and
  removes it. Randomising the event id hides the value, not the structure, and
  a page ``MutationObserver`` registered earlier sees the insertion.
- The page-scope and content-scope halves communicate over a ``CustomEvent`` on
  ``document``; a page that patches ``dispatchEvent``/``addEventListener``
  first observes that traffic.

Each of these follows from executing in the page's principal, not from a
particular wrapper. Removing them means moving execution into an isolated
world, which is what the stealth instrument is: that is why stealth is a
separate instrument rather than a hardening pass over legacy.

Legacy's detectability ceiling is architectural
-----------------------------------------------

Most of legacy's tells yield to ordinary engineering. Wrapper arity and name can
be copied from the native at no capture cost (PR `#1210
<https://github.com/openwpm/OpenWPM/pull/1210>`_). Prototype pollution, 11 extra
own properties on ``CanvasRenderingContext2D.prototype`` where the descent
materialises inherited members, is an implementation choice: hooking each
inherited member once on its owning prototype and attributing by ``this``
removes it, at a data-layout and attribution cost. Frame coverage is the same
kind of problem: more cases, each coverable.

What does not go away is the position. A page-world wrapper can patch only its
own realm's ``Function.prototype.toString``, so the unpatched intrinsic is
always one fresh realm away:
``iframe.contentWindow.Function.prototype.toString.call(fn)`` returns the
wrapper body. Keeping up means re-instrumenting every realm as it is created, a
race the instrument stays hidden in only as long as it arrives first.

Staying out of the page world removes the race. From its sandbox the stealth
instrument reads page objects through Xrays and exposes only what it chooses
through ``exportFunction``, so it never mutates a page intrinsic, and its
window actor instruments every window global when it is created, before the
page can reach it. Nothing in the page is hooked to learn of new frames (the
``D10-fp-*`` rows in :doc:`Stealth-Requirements`).

The claim covers the vectors the reliability paper names (``toString``,
prototype pollution, arity, name), not every conceivable tell; of those, only
the realm-local ``toString`` patch is structural to a page-world wrapper.

Migrating a settings file
-------------------------

Stealth settings name ``object`` by bare global name and list members as
explicit ``{depth, propertyNames}`` entries.
``openwpm/utilities/js_settings_migrator.py`` translates a legacy config into
the stealth shape by replaying the legacy descent over a live object graph, so
the result reflects what legacy would have instrumented. It reports every
legacy member the stealth config does not cover, plain-object nodes and
``navigator.sendBeacon`` among them, and exits non-zero when it does; that is
also how a study learns whether it depends on the recursion gap. Captured
``symbol`` values are unchanged. Details are under "Mechanical expansion" in
:doc:`Stealth-Instrumentation`.

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
