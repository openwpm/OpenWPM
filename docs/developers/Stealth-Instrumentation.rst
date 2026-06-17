Stealth JavaScript Instrumentation
==================================

Developer reference for ``stealth_js_instrument``: threat model, mechanism,
residual tells and configuration. How its data differs from ``js_instrument``
and why legacy is kept: :doc:`Stealth-and-Legacy-JS-Instruments`. Requirements
and the tests guarding them: :doc:`Stealth-Requirements`,
:doc:`Stealth-Validation`.

.. _stealth-threat-model:

Threat model
------------

Krumnow, Jonker & Karsch, *"Analysing and strengthening OpenWPM's reliability"*
(`arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_, 2022) show OpenWPM is
easily detectable and open to data-integrity attacks, and propose the
mitigations implemented here. The two are independent: detectability is a
property of the instrument's *footprint* (what it leaves visible in the page),
data integrity of the *record channel* (whether the page can reach the path
records travel on). An undetectable instrument on a page-reachable channel is
still disruptable, and a detectable one off it is not.

Out of scope: environment fingerprints that are not instrumentation artifacts
(screen/window position, font enumeration, WebGL deviations, timezone), and JS
delivered with a non-``.js`` MIME type or extension, which concerns the HTTP
instrument.

.. _legacy-detectability:

Detectability (a property of the legacy instrument)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Legacy runs in the page compartment, so its wrappers and footprint are
page-observable. Stealth avoids each artifact below; what it leaves is under
`Known residual tells`_.

Per-API tells, from wrapping in the page compartment:

- ``toString()`` **leak** — wrapped functions return their JS body instead of
  ``[native code]``. The most reliable tell, and inherent: a page can reach a
  sibling realm's ``Function.prototype.toString`` (e.g. via a same-origin
  iframe) that legacy has not patched, so no page-compartment patching closes
  it. Measured: :ref:`legacy-ceiling`.
- **Prototype pollution** — ancestor-prototype properties are flattened onto
  the first prototype (11 extra own properties on
  ``CanvasRenderingContext2D.prototype``), a structurally anomalous chain.
  Removable, at a data-layout cost: the flatten files an inherited member
  under the interface it was reached through. Hooking the owning prototype
  instead files it under the owner (an ``AnalyserNode`` and a ``GainNode``
  both report ``AudioNode.connect``), with the receiver's interface in a
  separate column, and ``collection_fingerprinting`` depends on the flatten
  for 11 of its 14 entries.

Global footprint, not tied to any wrapped API (hiding it: issue
`#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_):

- **Leaked globals** — ``window.jsInstruments``, ``instrumentFingerprintingApis``
  and ``getInstrumentJS`` exist in no real browser. The paper found 356 sites
  keying on them (CHEQ, reCAPTCHA, AdZouk).
- ``navigator.webdriver === true`` — the Selenium tell.
- **Error stacks** carry the legacy wrapper as an extra frame. It appears under
  the document's own URL, not ``moz-extension://``; the give-away is the
  wrapper's page-foreign function name.

The paper measured Selenium detection on ~14% of Tranco Top 100K front pages,
rising ~37% on subpages.

Data-integrity attacks (a property of the record channel)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These corrupt the dataset instead of blocking the crawler:

- **Event-dispatcher hijacking** — legacy ships records from the page to the
  extension via DOM ``CustomEvent``. A page can read the random event ID,
  overwrite ``document.dispatchEvent`` and drop all records.
- **Fake-data injection** — through the same hole a page emits events with
  OpenWPM's ID and writes arbitrary rows.
- **Unobserved iframes** — dynamically created iframes can run script before
  instrumentation is injected.

What stealth mode implements
----------------------------

The paper's §7 mitigations, adapted from CanvasBlocker:

1. **Native-looking wrappers.** Every replacement reaches the page through
   Firefox's privileged ``exportFunction`` (MDN: `Sharing objects with page
   scripts
   <https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Sharing_objects_with_page_scripts>`_,
   covering the Xray membrane, ``exportFunction`` and ``wrappedJSObject``).
   ``Function.prototype.toString`` prints the native source string from every
   realm and is itself never patched; ``.name`` matches; and, like a native
   method, the forwarder (a method definition) is not a constructor, so
   constructors (``Image``, ``OfflineAudioContext``, ...) are never replaced: a
   configured one is refused with a console error.

   ``.length`` matches because ``makeArityForwarder`` (``instrument.ts``)
   codegens, via ``new Function``, a forwarder declaring the native's number of
   parameters (clamped to ``[0, 256]``, and never 0 for an over-bound arity);
   Xray reads ``.length`` from the target. A naive ``arguments`` forwarder
   would report 0. The template takes a fixed integer, never page input, and
   forwarders are cached per arity. Guarded by D8b
   (:doc:`Stealth-Requirements`), which legacy trips.
2. **Per-prototype overwrites**, no flattening: only the instrumented members
   are redefined; ``constructor`` never is.
3. **No leaked globals.**
4. **No page-reachable call path.** Each native, captured from its descriptor
   (``value``/``get``/``set``) before any page script, is held as
   ``Function.prototype.call`` bound to it in a second sandbox with the page's
   principal (``pinNative`` in ``instrument.ts``, ``nativePinner`` in
   ``OpenWPMStealthChild.sys.mjs``) and invoked with the instrument sandbox's
   ``Reflect.apply``, never through ``.call``/``.apply`` looked up on a page
   object. A page that replaces ``Function.prototype.call``, ``apply`` or
   ``Reflect.apply`` neither observes the instrument nor gets handed the
   native (``hooks`` section of ``TestStealthNativeParity``). Arguments are read
   through Xrays, so recording runs no page getter, ``toJSON`` or ``Proxy``
   trap (what is kept: "Recorded values" under `Known residual tells`_).
5. **Untouched exceptions.** Exceptions from the native are not caught. The
   native runs in the page realm, so an exception is a page object (or the
   page's own thrown value), and ``exportFunction`` hands back the identical
   object. Its ``stack``, read by the page, has no extension frames:
   SpiderMonkey omits frames whose principal the reader does not subsume.
6. **Off-DOM messaging.** Records go from the content process to the parent
   over the process message manager, never the DOM, so ``dispatchEvent``
   hijacking cannot drop or forge them (:ref:`stealth-disruptability`). The
   parent derives a record's tab and frame from the window global it was made
   in and keeps that bookkeeping, so records made after the window global is
   gone (a removed frame's members, ``pagehide`` and ``unload`` handlers,
   members of a navigated-away document, across processes too) keep their
   attribution. A record from a window global the parent never saw is
   attributed to the claimed tab only if the sending process hosts a document
   in it, and to no tab otherwise. A record whose window global belongs to
   another process (only an instrument bug or a compromised content process
   produces one) is dropped.
7. **Every realm, from its creation.** A ``JSWindowActor`` observing
   ``content-document-global-created`` starts the instrument in every content
   window global as it is created, synchronously and before any script in it:
   including a frame's or popup's initial ``about:blank`` document, which a
   page can reach in the task that created it and no content script ever runs
   in (Firefox `bug 1415539
   <https://bugzilla.mozilla.org/show_bug.cgi?id=1415539>`_), and ``blob:``,
   ``data:`` and sandboxed documents. Because Gecko reports every new window
   global, no DOM API (``appendChild``, ``innerHTML``, ``document.write``,
   ``window.open``, ``contentWindow``, ...) is hooked to catch new frames.

   Each window global gets its own instrument sandbox, set up as Firefox sets
   up a content script's (``Cu.Sandbox`` in ``OpenWPMStealthChild.sys.mjs``):
   an expanded principal over the extension and the page, Xray views of page
   objects, ``exportFunction`` to give the page its members, and exemption from
   the page's CSP. The record ordinal and 500-record cap are per document, as
   in legacy. A same-origin document that reuses the global of its initial
   ``about:blank`` is not instrumented again: it keeps the members, as an
   uninstrumented Firefox keeps its natives, and they record under the document
   now in the window. Each call passes through one instrumented member and is
   recorded once.

   Members outlive their window, as natives do; pages commonly take pristine
   natives from a throwaway frame and remove it. When a window is destroyed,
   Firefox cuts every wrapper into it held by a system- or expanded-principal
   compartment (``WindowDestroyedEvent``, ``BrowserCompartmentMatcher``),
   including the instrument's sandbox, but not the page-principal sandbox of
   item 4, which is why the instrument's sandbox holds only the bound ``call``,
   never the native. Calls on a removed, navigated or closed window's members
   behave as in an uninstrumented Firefox (``TestStealthDeadRealm``); their
   attribution is under :ref:`frame attribution <stealth-frame-attribution>`.

   The actor, its process bootstrap and the ``stealthInstrument`` experiment
   API (which collects records and resolves their tab, frame and document) live
   in ``Extension/bundled/privileged/stealthInstrument/``. Study settings reach
   content processes through ``sharedData``; nothing is defined in the page.
   ``stealthInstrument.enable()`` rejects, and the browser fails to start, if
   any setup step throws. The extension is installed temporarily, so its XPI
   lies in the profile root, which the Linux content sandbox does not let
   content processes read; the bootstrap, a process script, opens it in each
   new process before the sandbox is applied (``bootstrap.js``). A process
   alive at install time cannot read it and is not instrumented: ``enable()``
   replaces the preallocated ones, and no crawled page loads into the
   remaining one, the startup ``about:blank`` tab's ``web`` process.

Key files: ``Extension/src/stealth/{actor,host,instrument,settings,error}.ts``
and ``Extension/bundled/privileged/stealthInstrument/``.
``TestStealthNativeParity`` (``test/test_pages/stealth_native_parity.html``)
checks items 1, 2, 4 and 5 differentially: each observation must be equal in an
uninstrumented Firefox and under stealth.

.. _stealth-residual-tells:

Known residual tells
~~~~~~~~~~~~~~~~~~~~

Page-observable with the bundled default surface, or gaps in what is recorded;
not closed. Most follow from a scripted function sitting between the page and
each instrumented native: stealth hides that the interposer is OpenWPM, not
that there is one, which puts it in the same class as a privacy extension such
as CanvasBlocker.

- **Interface resolution order** (`#1240
  <https://github.com/openwpm/OpenWPM/issues/1240>`_). Firefox defines a
  window's interface objects (``Navigator``, ``AudioContext``, ...) lazily, and
  ``Object.getOwnPropertyNames(window)`` lists resolved ones after unresolved
  ones, in resolution order. Instrumenting a prototype resolves its interface
  when the window global is created, so the first page script sees the default
  surface's interfaces (and their parents) already resolved, in
  ``settings.ts`` order: a stable signature for anyone who hashes the window's
  key list. Measured on Firefox 157: reaching the interface through an Xray
  resolves it on the page's window too; creating an instance or reaching its
  prototype through one resolves it; a deleted interface name is never
  resolved again and disappears from the key list; resolving everything
  eagerly would move every name. ``RESOLVED_BEFORE_PAGE_SCRIPT``
  (``test/test_stealth.py``) pins the names and checks nothing else moves
  before the first page script. Later, recording an element argument
  (``createMediaElementSource(el)``, ``drawFocusIfNeeded(el)``) reads its
  ancestors and siblings, resolving the interfaces of nodes the page has not
  touched (``Text``, ``Comment``, ``CharacterData``, ...).
- **Conversion error messages.** When a native fails to convert an argument
  (``localStorage.setItem(k, px)`` with an object lacking a usable
  ``toString``), SpiderMonkey names the offending expression only if the
  innermost scripted frame is the caller's and in the native's realm
  (``DecompileExpressionFromStack``, ``js/src/vm/BytecodeUtil.cpp``): "can't
  convert px to string". Under any JavaScript wrapper, stealth's or legacy's,
  that frame is the wrapper's, so the message falls back to the value's source
  ("can't convert Proxy to string"). The native still performs every
  conversion, in the same order, and throws the same page-realm error. Closing
  this needs an interposition with no scripted frame between page and native;
  ``exportFunction`` forwarders, bound functions and proxies either run our
  code inside that window or change the function's ``toString``.
- **Caller of a coerced callback.** In a sloppy page function an instrumented
  native calls synchronously (a ``toString`` passed to
  ``localStorage.setItem``, a ``valueOf`` passed to ``fillText``),
  ``arguments.callee.caller`` is ``null``; uninstrumented it is the page
  caller. SpiderMonkey hides the forwarder, a function of another compartment,
  as ``null`` (``CallerGetterImpl``, ``js/src/vm/JSFunction.cpp``).
- **Stack depth.** The forwarder adds frames, so the deepest recursion that
  succeeds through an instrumented call is slightly lower. Near the stack limit
  a call can fail where it succeeds uninstrumented; the error is then a
  page-realm ``InternalError`` or the ``InvalidStateError`` ``DOMException``
  Firefox substitutes at the sandbox boundary, never an object of the
  instrument's realms (``TestStealthOverflowErrors``).
- **Argument count limit.** The forwarder passes the receiver as an extra
  argument, so a call near SpiderMonkey's argument limit
  (``localStorage.getItem.apply(localStorage, new Array(500000))``) throws an
  ``InvalidStateError`` where it succeeds uninstrumented.
- **Deletable wrappers.** See :ref:`stealth-disruptability`.
- **Two webdriver overrides.** PR #1230 (``spoof_webdriver``) sets
  ``navigator.webdriver`` to ``false`` in every realm from its own window
  actor; with both enabled, the stealth ``webdriver`` override wraps that
  getter again.
- **Uninstrumented realms and surface.** Workers and worklets are not window
  globals, so their APIs are not instrumented and a page can fingerprint there
  unrecorded; ``OffscreenCanvas`` is not in the default surface, so canvas
  fingerprinting through it goes unrecorded on the main thread too.
  Fingerprinting counts are lower bounds
  (`#1245 <https://github.com/openwpm/OpenWPM/issues/1245>`_).
  ``navigator.webdriver`` is not exposed in workers.
- **Recorded values.** Only plain objects, arrays and typed arrays are copied
  (own data properties; typed arrays up to the value cap). Any other object is
  recorded as its brand (``[object Storage]``, ``[object Date]``), a ``Proxy``
  as ``[object Proxy]``: reading a host object's named properties can change
  its state (enumerating a ``Storage`` opens its database), and a ``Proxy``'s
  contents are reachable only through its traps. Legacy serializes in the page,
  running getters, ``toJSON`` and ``Proxy`` traps, and records their contents,
  so in the default surface stealth does not record the store contents legacy
  recorded on ``window.localStorage``/``sessionStorage`` gets, nor the SDP of
  ``RTCPeerConnection.localDescription``
  (`#1246 <https://github.com/openwpm/OpenWPM/issues/1246>`_).
  Xrays show only own data properties with plain-data values, so inside an
  object or array, function-, accessor- and ``Proxy``-valued entries are left
  out (``{id: 1, cb: fn}`` → ``{"id":1}``, ``[1, fn, 3]`` → ``[1,null,3]``), as
  are keys named after ``Object.prototype`` members (``toString``, ``valueOf``,
  ``hasOwnProperty``, ``constructor``); boxed primitives are ``{}`` and
  trailing holes are dropped. ``"FUNCTION"`` (or the source) is recorded only
  for a function passed directly as an argument or value. A call copies at
  most 128 values, 16 levels deep, across all its object arguments, and
  strings, keys and function sources up to 65 536 characters; the rest is
  ``TRUNCATED``. Non-object arguments are always recorded.
- **Assignments to getter-only properties** (``navigator.userAgent = x``) are
  not recorded; legacy records a ``set(failed)`` row.
- **top_level_url of a navigated-away document.** A call through a member of a
  navigated-away document is recorded with that document's ``document_url``
  but the tab's current top-level URL.

.. _stealth-performance:

Performance
~~~~~~~~~~~

The instrument adds overhead to every window it instruments, synchronously
while the window global is created (a frame's ``appendChild``, ``window.open``),
and to every instrumented call, which captures a JavaScript stack and reads
the receiver's interface; both grow with the instrumented surface.

The data path across the Xray membrane:

.. code-block:: text

   content process                                        | parent process
   JSWindowActor (content-document-global-created)       |
     -> per-window sandbox: startInstrument()            |
          -> exportFunction wrappers onto page prototypes |
   page calls a wrapped member                            |
     -> sandbox: logCall / notify                         |
     -> Services.cpmm (page cannot reach) ---------------> stealthInstrument API
                                                          |   -> background
                                                          |   -> javascript table

.. _stealth-configuring:

Configuring the instrumented surface
------------------------------------

.. code-block:: python

   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False  # both enabled raises ConfigError
   # Leave unset for the bundled fingerprinting default, or override:
   browser_params.stealth_js_instrument_settings = [
       {
           "object": "CanvasRenderingContext2D",   # bare global name (see below)
           "instrumentedName": "CanvasRenderingContext2D",
           "depth": 0,
           "logSettings": { ... },
       },
       ...
   ]

Each instrument has its own settings field: legacy ``js_instrument_settings``,
stealth ``stealth_js_instrument_settings``. Left ``None`` (the default), stealth
uses the bundled set in ``Extension/src/stealth/settings.ts``. When set, the list
is validated against ``schemas/stealth_js_instrument_settings.schema.json``
(`Entry fields`_; by ``clean_stealth_js_instrumentation_settings`` in
``openwpm/js_instrumentation.py``), written into ``browser_params.json`` and
handed to every content process through ``sharedData``
(``stealthInstrument.enable``); ``startInstrument`` (``stealth/instrument.ts``)
uses it when present, else the bundled default. The override that makes
``navigator.webdriver`` read ``false`` lives in the default; a custom
surface that needs it must include it.

.. _stealth-send-beacon:

``navigator.sendBeacon``
~~~~~~~~~~~~~~~~~~~~~~~~

Not wrapped by the default: wrapping it drops beacons a page sends from
``pagehide`` while its process shuts down (a closed tab or popup, a removed or
cross-process-navigated frame), which the site can notice. Firefox stops such a
script at its next interrupt check, and through any JavaScript wrapper that
check comes before the native, so wrapping any native that runs in
``pagehide`` during process teardown loses the call the same way. Instead,
enable ``http_instrument`` to record the beacon request including its body
(resource type ``beacon``), and ``callstack_instrument`` for its JavaScript
origin, captured at the network level without a wrapper, once `#1178
<https://github.com/openwpm/OpenWPM/pull/1178>`_ restores it (enabling it raises
``ConfigError`` until then). To wrap it anyway, list ``sendBeacon`` in a custom
surface and accept the loss. Validation warns when a custom surface wraps it,
and the settings migrator reports it as untranslated (non-zero exit), both with
the reason in ``STEALTH_UNWRAPPED_MEMBERS`` (``openwpm/js_instrumentation.py``).

.. _stealth-object-naming:

The ``object`` naming convention (differs from legacy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stealth resolves ``object`` as a **bare global name**, looked up on the
page's global scope (``context.wrappedJSObject[object]``):
``"CanvasRenderingContext2D"``, ``"Navigator"``, ``"Storage"``,
``"document"``. Legacy ``js_instrument_settings`` instead use a ``window``
path (``"window['CanvasRenderingContext2D'].prototype"``,
``"window.document"``) produced by ``clean_js_instrumentation_settings``,
which would resolve to nothing, so validation rejects any ``object`` that is
not a bare name.

**Instance vs. prototype properties.** A named constructor is instrumented on
its ``.prototype``, where the native accessors live. ``document`` and ``window``
are instances, and where their accessors live depends on the attribute.
``window.name``, ``window.localStorage`` and ``window.sessionStorage`` are
native **own** accessors of the ``window`` instance, not of
``Window.prototype`` (in a clean Firefox,
``getOwnPropertyDescriptor(Window.prototype, "name")`` is ``undefined`` and
``getOwnPropertyDescriptor(window, "name")`` a native accessor: ``window.name``
is a ``[Replaceable]`` WebIDL attribute), so they are instrumented at inner
**depth 0** on the instance: ``{ object: "window", propertiesToInstrument:
[{ depth: 0, propertyNames: ["name", "localStorage", "sessionStorage"] }] }``
redefines the native accessors in place. Depth counts from the instance on both
the named-list and the instrument-everything path, so
``Document.prototype.cookie`` is depth 2 from ``document``. A name inherited at
the configured depth is refused, and an entry that instruments no member is
reported in the browser console. Because the descriptor is swapped in place,
with ``exportFunction`` getters/setters reporting ``[native code]``,
``getOwnPropertyDescriptor`` still returns a native-shaped own accessor: this is
why instrumenting ``window.name`` is undetectable. The default instruments
exactly ``name``, ``localStorage`` and ``sessionStorage`` on ``window``, not
layout properties (``innerWidth``, ``innerHeight``, ``screenX``, …), which fire
constantly and would inflate capture volume without tracking signal.

.. _stealth-log-settings:

Entry fields
~~~~~~~~~~~~

``schemas/stealth_js_instrument_settings.schema.json`` defines the fields of an
entry, and validation rejects any other. The stealth instrument
(``Extension/src/stealth/instrument.ts``) reads them as follows.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Stealth behaviour
   * - ``object``
     - Bare global name (:ref:`stealth-object-naming`).
   * - ``instrumentedName``
     - Prefix of the recorded ``symbol``.
   * - ``depth``
     - Prototype-chain offset from the resolved ``object``, default 0. With an
       empty ``propertiesToInstrument``, every own member of the prototypes
       from offset 0 to ``depth`` is instrumented, and non-existing names are
       added at ``depth``.
   * - ``logSettings.propertiesToInstrument``
     - Names (own members at offset 0) or ``{depth, propertyNames}`` (own
       members of the prototype ``depth`` steps up the chain); empty means
       every own member up to the entry's ``depth``.
       ``excludedProperties``/``overwrittenProperties`` are filtered out on
       both paths.
   * - ``logSettings.excludedProperties``
     - Skipped on the named-list and the instrument-everything path.
   * - ``logSettings.overwrittenProperties``
     - Value overwritten on read (e.g. ``navigator.webdriver`` reads ``false``);
       accessors only, a method listed here is refused.
   * - ``logSettings.nonExistingPropertiesToInstrument``
     - Names absent from the target get a synthesized, ``[native
       code]``-reporting accessor (backed by a closure variable), so a study can
       capture access to decoy names.
   * - ``logSettings.logCallStack``
     - Per-object call-stack capture (page frames only; never
       ``moz-extension://``).
   * - ``logSettings.logFunctionsAsStrings``
     - Function values serialised as their source instead of ``"FUNCTION"``.
   * - ``logSettings.logFunctionGets``
     - A getter returning a **function** emits a ``get(function)`` row (and no
       plain ``get``).
   * - ``logSettings.receiverInterfaces``
     - For a method hooked once on a shared prototype, the receiver interfaces
       (at least one) whose calls are recorded
       (`Interface-attributed shared-prototype capture`_).

The default leaves ``logFunctionGets`` and
``nonExistingPropertiesToInstrument`` off; a custom surface can enable them. A
legacy ``js_instrument_settings`` config translates with the migrator
(`Migrating legacy settings`_).

``TestStealthLogSettings`` covers ``logFunctionGets`` and
``nonExistingPropertiesToInstrument``, with an undetectability check on the
synthesized accessor (``stealth_non_existing_props.html``), and
``test_stealth_settings_reject_unknown_fields`` the rejection of unknown fields,
config-only (``pyonly``).

Decoy names from ``nonExistingPropertiesToInstrument`` are page-observable by
design: they look native, so they do not identify OpenWPM, but a page that
knows a name should not exist on a real Firefox object can notice it. The names
are study-chosen rather than an OpenWPM signature, and the default has none.

.. _stealth-disruptability:

Disruptability: what the off-DOM channel buys
---------------------------------------------

Stealth's disruptability advantage over legacy is the off-DOM record channel
(item 6 of `What stealth mode implements`_), which defeats the
`Data-integrity attacks (a property of the record channel)`_ on legacy's
``dispatchEvent``/``eventId``: a page can neither suppress (X1) nor forge (X2)
records. ``TestStealthDisruption`` shows both directions
(:doc:`Stealth-Requirements`).

Deleting or redefining a wrapped member hides no call. Wrappers keep the
native descriptor (``instrumentFunction`` and ``instrumentGetterSetter`` in
``instrument.ts`` swap only ``value``, ``get`` or ``set``), so a page can
``delete`` or redefine them as it could the natives, but the natives stay out of
its reach (item 4 of `What stealth mode implements`_). A page that deletes a
member loses the API; one that replaces it with its own code (a polyfill, shim
or blocker) has its callers run that code, which is not a browser API call.
Any native call still goes through a forwarder: a copy of the member taken
before the delete records
(``TestStealthRecordIntegrity::test_call_hidden_behind_a_deleted_member``).
Locking the descriptors down (``configurable: false``, ``writable: false``,
frozen prototypes) would therefore buy nothing and be page-observable, so none
is applied.

Test coverage
-------------

``test/test_stealth.py`` is requirement-driven: :doc:`Stealth-Requirements`
maps each detectability (D), disruptability (X), attribution (A1) and
configurability (C1) requirement to its tests, and :doc:`Stealth-Validation`
maps every way the instrument could taint a study to its guard.

.. _stealth-migrator:

Migrating legacy settings
-------------------------

Stealth hooks only the prototypes and globals an entry names and never recurses
into the objects a getter returns (``recursive`` is rejected as an unknown
field): those ``Object``/``Array`` instances have no global interface
prototype, so the only place for an accessor is the returned page instance
itself, a page-observable own-property mutation. A recursive legacy config is
translated instead by ``openwpm/utilities/js_settings_migrator.py``. It
launches a lightweight Firefox, replays the exact legacy descent
(``instrumentObject`` in ``Extension/src/lib/js-instruments.ts``) over the live
object graph, and emits one flat entry per reached node: ``object`` is the
node's ``constructor.name`` (the bare global prototype stealth hooks),
``instrumentedName`` the legacy symbol path. It covers the per-node
own-prototype names and reports the rest (`Coverage is not loss-free`_).

.. code-block:: bash

   python -m openwpm.utilities.js_settings_migrator YOUR_LEGACY_CONFIG.json \
       --output stealth_config.json

The output is ready for ``browser_params.stealth_js_instrument_settings``.

Coverage is not loss-free
~~~~~~~~~~~~~~~~~~~~~~~~~

The mismatch runs both ways:

- **Stealth covers more for object-valued properties.** Under recursion legacy
  suppresses the plain ``get`` of an object-valued property it descends into
  (the recursion branch of ``instrumentObject`` returns the child without that
  ``get`` row); the flat entry has nothing to suppress and logs it. The parity
  test asserts stealth set B ⊇ (legacy set A − reported gaps), not equality.
- **Legacy covers names stealth does not.** Each is returned as an
  ``UntranslatedEntry`` (second element of the ``legacy_settings_to_stealth``
  return tuple) and logged, and any of them makes the CLI exit non-zero, so a
  pipeline cannot mistake an incomplete translation for a clean one:

  1. **Untranslatable node** — ``constructor.name`` is ``Object``/``Array``/falsy
     (e.g. ``navigator.languages``): no global interface prototype to hook.
  2. **Universal-prototype inherited member, or inherited non-method member** —
     legacy's ``Object.getPropertyNames(instance)`` covers the instance's own
     names plus the whole prototype chain to ``null``; the emitted ``depth: 0``
     entry (``getPropertyNamesPerDepth(proto, 0)``) covers only the leaf
     prototype's own names. Not translated: members of a **universal**
     prototype (``Object.prototype``/``Function.prototype``/``Array.prototype``
     — ``toString``, ``valueOf``, …; hooking them fires on virtually every
     receiver), and inherited **accessors / data members** (e.g.
     ``Document.prototype.URL``), whose receiver cannot be filtered at call
     time as a method's can. Inherited methods of a real interface prototype
     are captured instead (`Interface-attributed shared-prototype capture`_).
  3. **Resolution failure** — a legacy ``object`` string that does not
     ``eval`` to a live node.
  4. **Unwrapped by design** — ``navigator.sendBeacon``
     (`navigator.sendBeacon`_).

.. _stealth-receiver:

Interface-attributed shared-prototype capture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An inherited method owned by a real global interface prototype (e.g.
``addEventListener`` on ``EventTarget.prototype``, reached via a DOM element,
``navigator.permissions``, ``XMLHttpRequest``, ``window.document``, …) becomes,
per ``(owner interface, method)``, one entry that hooks the method once on the
owner's prototype, with ``receiverInterfaces`` listing the leaf interfaces that
reached it:

.. code-block:: json

   {
     "object": "EventTarget",
     "instrumentedName": "EventTarget",
     "depth": 0,
     "logSettings": {
       "propertiesToInstrument": ["addEventListener"],
       "receiverInterfaces": ["HTMLDocument", "HTMLDivElement"],
       "...": "..."
     }
   }

Every call, get and set records its receiver's interface in the ``receiver``
column of the ``javascript`` table. ``getReceiverInterfaceName``
(``Extension/src/stealth/instrument.ts``) reads it from ``this`` — an Xray,
which shows the native view and hides page-side modifications — as
``Object.getPrototypeOf(this).constructor.name``, falling back to
``this.constructor.name``. It is the genuine interface name even when the page
has redefined ``constructor`` on the instance or its prototype (verified
against ``js/xpconnect/wrappers/XrayWrapper.cpp`` and measured in Firefox). The
read defines nothing on the page and triggers no page getter; measured on
Firefox 157, it resolves no interface name on the page either, as the page's
own call that produced the receiver already did. ``receiver`` is NULL only when
no interface name can be read.

``symbol`` stays the static shared-prototype method
(``EventTarget.addEventListener``), so post-processing filters
``WHERE symbol='EventTarget.addEventListener' AND receiver='HTMLDivElement'``
instead of parsing ``symbol``, or maps rows to legacy's ``symbol`` with
``db_utils.legacy_symbol`` (:ref:`stealth-what-changes`). With
``receiverInterfaces`` the sandbox also filters: a call is recorded only if its
receiver's interface is listed, and others are dropped before any record is
emitted, so there is no site-wide flood to discard later. The filter applies to
methods only.

Attribution is interface-level by design: two instances of one interface are
not distinguished. ``TestStealthSharedPrototypeCapture`` and
``TestStealthSweepSharedPrototype`` cover the capture, the filter and the
unfiltered case, ``TestStealthDefaultSurface`` the receiver of a call, get and
set under the default surface.

``TestStealthRecursiveSweepParity`` runs a ``recursive`` config under legacy
(set A), sweeps it, runs the result under stealth (set B), and asserts B covers
A modulo the reported gaps and that every legacy symbol missing from B is
reported. One test drives a universal-prototype member
(``navigator.permissions.toString``, from ``Object.prototype``) end-to-end to
the report; ``TestStealthSweepSharedPrototype`` shows ``addEventListener``
reached via ``window.document`` becoming an ``EventTarget`` shared-prototype
entry.

Opt-in: capturing universal-prototype methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Universal-prototype methods (``Object.prototype`` / ``Function.prototype`` /
``Array.prototype`` — ``toString``, ``valueOf``, ``hasOwnProperty``, …) stay
untranslated by default (class 2 above): hooking ``Object.prototype.toString``
fires on every object's ``toString()`` page-wide, high overhead and volume for
essentially no tracking signal. Legacy ``recursive`` hooked them (it walked the
full chain); for strict parity, opt in:

- **Library:** ``legacy_settings_to_stealth(..., capture_universal_prototype_members=True)``.
- **CLI:** ``--capture-universal-members``.

The sweep then emits one consolidated ``{object: "Object" | "Function" |
"Array", depth: 0, …}`` entry listing every reached universal method, with
``receiverInterfaces`` covering all leaf interfaces that reached them (e.g.
``Navigator``, ``Permissions``). ``{object: "Object"}`` resolves to the page's
``Object.prototype`` via ``wrappedJSObject["Object"].prototype``, as for real
interfaces, so no extension change is involved, and the receiver filter limits
records to those interfaces.

.. warning::

   This wraps every ``toString``; enable it only for strict
   legacy-``recursive`` parity. Non-method universal members (accessors such as
   ``__proto__``) stay untranslated regardless, because the receiver filter
   applies only to methods. With the flag off, no ``Object``/``Array`` entry is
   emitted. ``TestStealthSweepUniversalPrototypeCapture`` covers both settings.
