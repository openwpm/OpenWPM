Stealth JavaScript Instrumentation
==================================

This document describes the *stealth* JavaScript instrumentation mode added by
``stealth_js_instrument``, the threat model it addresses, and exactly how its
data capture differs from the legacy ``js_instrument`` mode. The audience is
OpenWPM developers: it is an internal architecture reference — mechanism,
implementation constraints, and maintenance notes — not a researcher-facing
decision guide.

Background: why stealth instrumentation exists
----------------------------------------------

The design follows Krumnow, Jonker & Karsch, *"Analysing and strengthening
OpenWPM's reliability"* (`arXiv:2205.08890
<https://arxiv.org/abs/2205.08890>`_, 2022). That paper shows OpenWPM is
both **easily detectable** and **vulnerable to data-integrity attacks**, and
proposes the mitigations implemented here.

The paper splits the problem into two **independent** families. They are
distinct mechanisms with distinct root causes — neither follows from the other.
Detectability is about the instrument's *footprint* (what it leaves visible in
the page); the data-integrity attacks are about the *record channel* (whether the
page can reach the path records travel on). A change that fixes one does not
imply the other.

Detectability (a property of the legacy instrument)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Detectability is a property of the **legacy** instrument: it runs in the page
compartment, so its wrappers and footprint are page-observable. (Stealth avoids
each of the artifacts below; what it does leave is listed under `Known residual
tells`_.) The artifacts a page can key on, and which are inherent versus
improvable, are:

**Per-API surface — the tells that follow from wrapping in the page
compartment. These are not uniform: one is structural, the other is an
implementation choice.**

- ``toString()`` **leak** — wrapped functions return their JS body instead of
  ``[native code]``. The single most reliable tell, and the one that is genuinely
  **inherent**: a page can reach a *sibling realm's* ``Function.prototype.toString``
  (e.g. via a same-origin iframe) that legacy has not patched, so no amount of
  page-compartment patching closes it. Measured, not theorised — see
  :doc:`Stealth-and-Legacy-JS-Instruments`.
- **Prototype pollution** — properties from ancestor prototypes are flattened
  onto the first prototype, producing a structurally anomalous chain. This one is
  **removable but costly, not a second structural wall**: the flatten is
  load-bearing for legacy's per-interface attribution of *inherited* members.
  Hooking the owning prototype instead collapses sibling attribution (an
  ``AnalyserNode`` and a ``GainNode`` both report ``AudioNode.connect``), and
  ``collection_fingerprinting`` depends on the flatten path for 11 of its 14
  entries. Dropping it is an implementation choice legacy could make at a
  data-layout and attribution-granularity cost.

**Global footprint — not tied to any wrapped API; might be hidden better
(issue** `#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_ **):**

- **Leaked globals** — ``window.jsInstruments``, ``instrumentFingerprintingApis``,
  and ``getInstrumentJS`` exist in no real browser. The paper found 356 sites
  keying on exactly these (CHEQ, reCAPTCHA, AdZouk).
- ``navigator.webdriver === true`` — the Selenium tell.
- **Error stack traces** carrying the legacy wrapper as an extra frame. Because
  legacy runs in the page compartment, that frame appears under the document's own
  URL (**not** ``moz-extension://``); the give-away is the wrapper's page-foreign
  function name, not the URL scheme.

The paper measured **~14% of Tranco Top 100K front pages** running Selenium
detection, rising ~37% on subpages.

Data-integrity attacks (a property of the record channel)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These silently corrupt a dataset rather than merely blocking the crawler. They
target the **record channel**, independently of detectability:

- **Event-dispatcher hijacking** — legacy OpenWPM ships instrumentation data
  page→extension via DOM ``CustomEvent``. A page can read the random event ID,
  overwrite ``document.dispatchEvent``, and drop all instrumentation messages.
- **Fake-data injection** — the same hole lets a page emit events with
  OpenWPM's ID and write arbitrary rows into the dataset.
- **Unobserved iframes** — dynamically-created iframes can execute before
  instrumentation is injected.

What stealth mode implements
----------------------------

Stealth mode is a direct implementation of the paper's §7 mitigations
(adapted from CanvasBlocker's approach):

1. **Native-looking wrappers.** Every replacement is handed to the page
   through Firefox's privileged
   ``exportFunction`` (see MDN's `Sharing objects with page scripts
   <https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Sharing_objects_with_page_scripts>`_,
   which covers the Xray membrane, ``exportFunction`` and ``wrappedJSObject``).
   The page sees a native function: ``Function.prototype.toString`` prints the
   native source string from every realm, ``.name`` and ``.length`` match, and
   like a native method it is not a constructor (the forwarder is a method
   definition). Constructors (``Image``, ``OfflineAudioContext``, ...) are
   therefore never replaced: a configured one is refused with a console error.
   ``Function.prototype.toString`` itself is never patched.
2. **Per-prototype overwrites** (no flattening) eliminate prototype pollution.
   Only the instrumented members are redefined; ``constructor`` is never
   replaced.
3. **No leaked globals**; the page context stays clean.
4. **No page-reachable call path.** The instrument calls each native through
   ``Function.prototype.call`` bound to it, taken from a sandbox of its own
   (``pinNative``), never through ``.call``/``.apply`` looked up on a page
   object, so a page that replaces ``Function.prototype.call``, ``apply`` or
   ``Reflect.apply`` neither observes the instrument nor gets handed the
   native. Arguments are recorded by reading them through Xrays: plain
   objects, arrays and typed arrays by their own data properties, every other
   object by its brand, so recording runs no page getter, ``toJSON`` or
   ``Proxy`` trap.
5. **Untouched exceptions.** The instrument does not catch exceptions from the
   native. The native runs in the page realm, so an exception is a page object
   (or the page's own thrown value) and ``exportFunction`` hands it back as the
   identical object. Its ``stack`` as read by the page contains no extension
   frames because SpiderMonkey omits frames whose principal the reader does not
   subsume.
6. **Off-DOM messaging** — records go from the content process to the parent
   over the process message manager, never through the DOM, so
   ``dispatchEvent`` hijacking cannot drop or forge them. The parent
   authenticates a record by the window global it claims to come from: that
   window global must belong to the sending process, or the record is dropped.
   Its tab and frame are then remembered, so records made after the window
   global is gone (a removed frame's members, a document's ``pagehide`` and
   ``unload`` handlers, members of a document navigated away, across processes
   too) keep that attribution. A record from a window global the parent never
   saw is attributed to the claimed tab only if the sending process hosts a
   document in it, and to no tab otherwise. This is the channel
   that gives stealth its disruptability advantage; see `Disruptability: what
   the off-DOM channel does and does not buy`_.
7. **Every realm, from its creation** — a ``JSWindowActor`` observing
   ``content-document-global-created`` starts the instrument in every content
   window global as it is created, synchronously and before any script in it.
   That includes a frame's or popup's initial ``about:blank`` document, which
   a page can reach in the task that created it and which no content script
   ever runs in (Firefox `bug 1415539
   <https://bugzilla.mozilla.org/show_bug.cgi?id=1415539>`_), and ``blob:``,
   ``data:`` and sandboxed documents. Nothing in the page is hooked to learn of
   new frames.

   Each window global gets its own sandbox, with the expanded [extension, page]
   principal a content script gets, Xrays, export helpers and the window as
   prototype; its record ordinal and 500-record cap are per realm. When a
   same-origin document reuses the global of its initial ``about:blank``
   document, the global is not instrumented again: the document keeps the
   members, as an uninstrumented Firefox keeps its natives, and they record
   under the document now in the window. Each call therefore passes through
   one instrumented member and is recorded once.

   Members outlive their window, as natives do. Pages commonly take pristine
   natives from a throwaway frame and remove it; when a window is destroyed,
   Firefox cuts every wrapper into it that a system- or expanded-principal
   compartment holds (``WindowDestroyedEvent``, ``BrowserCompartmentMatcher``),
   which includes the instrument's sandbox. So the sandbox never holds a
   native: it holds ``Function.prototype.call`` bound to the native, owned by a
   second sandbox with the page's own principal, which Firefox leaves alone.
   Calls on a removed, navigated or closed window's members behave as in an
   uninstrumented Firefox and are recorded under that window's last document
   URL (``TestStealthDeadRealm``).

   The actor, its process bootstrap and the ``stealthInstrument`` experiment
   API that collects records and resolves their tab, frame and document live
   in ``Extension/bundled/privileged/stealthInstrument/``. Study settings reach
   content processes through ``sharedData``; nothing is defined in the page.
   ``stealthInstrument.enable()`` rejects, and the browser fails to start, if
   any step of this setup throws. The bootstrap needs no acknowledgement: a
   process receives it on the same ordered IPC channel as, and before, the
   actor registration, and a process launched later runs it before any
   document. A process that does not run process scripts gets no
   instrumentation; on Firefox 155 the only one seen is the ``web`` process of
   the startup ``about:blank`` tab, which no crawled page was loaded into.

Key files: ``Extension/src/stealth/{actor,host,instrument,settings,error}.ts``
and ``Extension/bundled/privileged/stealthInstrument/``.

``TestStealthNativeParity`` (``test/test_pages/stealth_native_parity.html``) is
the differential check for items 1, 2, 4 and 5: it records each observation in
an uninstrumented Firefox and under stealth and requires them to be equal.

Known residual tells
~~~~~~~~~~~~~~~~~~~~

These are page-observable with the bundled default surface, or are gaps in
what is recorded, and are not closed. Most follow from a scripted function
sitting between the page and each instrumented native: stealth hides that the
interposer is OpenWPM, not that there is one, which puts it in the same class
as a privacy extension such as CanvasBlocker.

- **Interface resolution order.** Firefox defines a window's interface objects
  (``Navigator``, ``AudioContext``, ...) lazily, and
  ``Object.getOwnPropertyNames(window)`` lists the resolved ones after the
  unresolved ones, in the order they were resolved. Instrumenting a prototype
  resolves its interface when the window global is created, so the first page
  script sees the default surface's interfaces (and their parents) already
  resolved, in ``settings.ts`` order: a stable signature for anyone who hashes
  the window's key list. This is a
  known open issue, tracked in
  `#1240 <https://github.com/openwpm/OpenWPM/issues/1240>`_. Measured on
  Firefox 155: reaching the interface through an Xray resolves it on the
  page's window too; creating an instance or reaching its prototype through one
  resolves it; a deleted interface name is never resolved again and disappears
  from the key list; and resolving everything eagerly would move every name.
  The names are pinned in ``RESOLVED_BEFORE_PAGE_SCRIPT``
  (``test/test_stealth.py``), which checks that nothing else moves.
- **Conversion error messages.** When a native fails to convert an argument
  (``localStorage.setItem(k, px)`` with an object that has no usable
  ``toString``), SpiderMonkey names the offending expression only if the
  innermost scripted frame is the caller's and in the native's realm
  (``DecompileExpressionFromStack``, ``js/src/vm/BytecodeUtil.cpp``): "can't
  convert px to string". Under any JavaScript wrapper, stealth's or legacy's,
  that frame is the wrapper's, so the message falls back to the value's source
  ("can't convert Proxy to string"). The native still performs every
  conversion itself, in the same order, and throws the same page-realm error.
  Closing this needs an interposition with no scripted frame between the page
  and the native; ``exportFunction`` forwarders, bound functions and proxies
  either run our code inside that window or change the function's
  ``toString``.
- **Caller of a coerced callback.** In a sloppy page function that an
  instrumented native calls synchronously (a ``toString`` passed to
  ``localStorage.setItem``, a ``valueOf`` passed to ``fillText``),
  ``arguments.callee.caller`` is ``null``; uninstrumented it is the page
  caller. SpiderMonkey hides the forwarder, a function of another
  compartment, as ``null`` (``CallerGetterImpl``, ``js/src/vm/JSFunction.cpp``).
- **Stack depth.** The forwarder adds frames, so the deepest recursion that
  still succeeds through an instrumented call is slightly lower. Near the
  stack limit a call can fail where it succeeds uninstrumented; the error is
  then a page-realm ``InternalError`` or the ``InvalidStateError``
  ``DOMException`` Firefox substitutes at the sandbox boundary, never an
  object of the instrument's realms (``TestStealthOverflowErrors``).
- **Argument count limit.** The forwarder passes the receiver as an extra
  argument, so a call with close to SpiderMonkey's argument limit
  (``localStorage.getItem.apply(localStorage, new Array(500000))``) throws an
  ``InvalidStateError`` where it succeeds uninstrumented.
- **Deletable wrappers.** See `Disruptability: what the off-DOM channel does and
  does not buy`_.
- **Two webdriver overrides.** PR #1230 (``spoof_webdriver``) sets
  ``navigator.webdriver`` to ``false`` in every realm from its own window
  actor; if both are enabled, the stealth ``webdriver`` override wraps that
  getter again.
- **Uninstrumented realms.** Workers and worklets are not window globals, so
  their APIs (e.g. ``OffscreenCanvas`` in a worker) are not instrumented. A page can
  run its fingerprinting there and nothing is recorded. ``navigator.webdriver``
  is not exposed in workers.
- **Recorded values.** Only plain objects, arrays and typed arrays are copied
  (from their own data properties, typed arrays up to the value cap); any
  other object is recorded as its brand, such as ``[object Storage]`` or
  ``[object Date]``, and a ``Proxy`` as ``[object Proxy]``: reading a host
  object's named properties can change its state (enumerating a ``Storage``
  opens its database), and a ``Proxy``'s contents are only reachable through
  its traps. Legacy records their contents. Objects are copied through Xrays,
  which show only own data properties whose values are plain data: inside an
  object or array, function-, accessor- and ``Proxy``-valued entries are left
  out (``{id: 1, cb: fn}`` → ``{"id":1}``, ``[1, fn, 3]`` → ``[1,null,3]``),
  as are keys named after ``Object.prototype`` members (``toString``,
  ``valueOf``, ``hasOwnProperty``, ``constructor``); boxed primitives are
  ``{}`` and trailing holes are dropped. ``"FUNCTION"`` (or the source) is
  recorded only for a function passed directly as an argument or value. A
  call copies at most 128 values, 16 levels deep, across all its object
  arguments, and strings, keys and function sources up to 65 536 characters;
  the rest is ``TRUNCATED``. Arguments that are not objects are always
  recorded.
- **Assignments to getter-only properties** (``navigator.userAgent = x``) are
  not recorded; legacy records a ``set(failed)`` row.
- **top_level_url of a navigated-away document.** A call through a member of a
  document that has been navigated away is recorded with that document's
  ``document_url`` but the tab's current top-level URL.
- **Record cap and ordinal on a reused window global.** A same-origin document
  that reuses the global of its initial ``about:blank`` continues that global's
  ordinal and its 500-record cap per script and symbol.

Performance
~~~~~~~~~~~

The instrument adds overhead to every window it instruments, synchronously
while the window global is created (a frame's ``appendChild``, ``window.open``),
and to every instrumented call, which captures a JavaScript stack; both grow
with the instrumented surface.

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

Enabling stealth mode
---------------------

.. code-block:: python

   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False  # mutually exclusive — see below

``stealth_js_instrument`` and ``js_instrument`` **cannot both be enabled** on the
same browser; doing so raises ``ConfigError``. Both instruments are
runtime-configurable — legacy via ``js_instrument_settings``, stealth via
``stealth_js_instrument_settings`` (see `Configuring the instrumented surface`_).
The two instruments differ on two independent axes — detectability (footprint)
and disruptability (record channel) — both treated below; legacy is worse on
each, stealth in exchange has the capability gaps documented under `Data capture:
differences from legacy js_instrument`_.

Configuring the instrumented surface
------------------------------------

The stealth surface is **runtime-configurable** via
``browser_params.stealth_js_instrument_settings``:

.. code-block:: python

   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False
   # Leave unset to use the bundled fingerprinting default, or override:
   browser_params.stealth_js_instrument_settings = [
       {
           "object": "CanvasRenderingContext2D",   # bare global name (see below)
           "instrumentedName": "CanvasRenderingContext2D",
           "depth": 0,
           "logSettings": { ... },
       },
       ...
   ]

When the field is ``None`` (the default), the instrument uses the bundled set in
``Extension/src/stealth/settings.ts``, so the out-of-the-box behaviour is
unchanged. When set, the list is validated against
``schemas/js_instrument_settings.schema.json`` (by
``clean_stealth_js_instrumentation_settings`` in ``openwpm/js_instrumentation.py``),
written into ``browser_params.json``, and handed to every content process
through ``sharedData`` (``stealthInstrument.enable``). ``startInstrument``
(``stealth/instrument.ts``) uses it when present and otherwise falls back to the
bundled default. The ``Navigator.webdriver → false`` override lives in
the default; a custom surface that needs it must include it explicitly.

``navigator.sendBeacon`` is deliberately not wrapped by the default: wrapping
it drops beacons a page sends from ``pagehide`` while its process shuts down (a
closed tab or popup, a removed or cross-process-navigated frame), which the
site can notice. Firefox stops such a script at its next interrupt check, and
through any JavaScript wrapper that check comes before the native; wrapping
any native that runs in ``pagehide`` during process teardown loses the call
the same way. Instead, enable ``http_instrument`` to record the beacon request
including its body (resource type ``beacon``), and ``callstack_instrument``
for its JavaScript origin, captured at the network level without a wrapper,
once `#1178 <https://github.com/openwpm/OpenWPM/pull/1178>`_ restores it
(enabling it raises ``ConfigError`` until then). To wrap it anyway, list
``sendBeacon`` in a custom ``stealth_js_instrument_settings`` surface and
accept the loss. Validation warns when a custom surface wraps it, and the
settings migrator reports it as untranslated (non-zero exit), both with the
reason in ``STEALTH_UNWRAPPED_MEMBERS`` (``openwpm/js_instrumentation.py``).

The ``object`` naming convention (differs from legacy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stealth resolves ``object`` as a **bare global name** — the property is looked up
directly on the page's global scope (``context.wrappedJSObject[object]``). Use
``"CanvasRenderingContext2D"``, ``"Navigator"``, ``"Storage"``, ``"document"``, etc.

This is **not** the legacy convention. Legacy ``js_instrument_settings`` express
``object`` as a dotted/bracketed ``window`` path
(``"window['CanvasRenderingContext2D'].prototype"``, ``"window.document"``)
produced by ``clean_js_instrumentation_settings``. The two formats are
intentionally separate: the legacy path is untouched, and stealth settings are
supplied in the stealth shape directly.

**Instance vs. prototype properties.** For most objects the named global is a
constructor and stealth instruments its ``.prototype`` (where the native accessors
live). Some globals are *instances*, though — ``document`` and ``window`` — and the
location of their accessors depends on the attribute. ``window.name``,
``window.localStorage`` and ``window.sessionStorage`` are native **own** accessor
properties of the ``window`` *instance* itself, **not** of ``Window.prototype``
(verified against a clean Firefox: ``getOwnPropertyDescriptor(Window.prototype,
"name")`` is ``undefined`` while ``getOwnPropertyDescriptor(window, "name")`` is a
native accessor — ``window.name`` is a ``[Replaceable]`` WebIDL attribute). They
must therefore be instrumented at inner **depth 0**, targeting the instance
directly. For example,
``{ object: "window", propertiesToInstrument: [{ depth: 0, propertyNames:
["name", "localStorage", "sessionStorage"] }] }`` resolves the ``window``
instance and redefines the native accessors **in place** on it. Depth counts
from the instance on both the named-list and the instrument-everything path, so
``Document.prototype.cookie`` is depth 2 from ``document``. A name that is
inherited at the configured depth is refused, and an entry that instruments no
member is reported in the browser console. Because the instrument swaps the descriptor in place on the
very object where the browser natively defines it — with ``exportFunction``-backed
getters/setters that report ``[native code]`` — ``getOwnPropertyDescriptor`` still
returns a native-shaped own accessor on the instance and the masquerade is
preserved (this is why instrumenting ``window.name`` is undetectable). The default
surface deliberately restricts the ``window`` list to
exactly ``name``, ``localStorage``, and ``sessionStorage``; it does **not**
instrument layout/dimension properties (``innerWidth``, ``innerHeight``,
``screenX``, …), which fire constantly and would inflate capture volume without
adding tracking signal.

Data capture: differences from legacy ``js_instrument``
-------------------------------------------------------

The bundled default surface (``Extension/src/stealth/settings.ts``) is a curated,
stealth-shaped configuration rather than a 1:1 copy of the legacy
``collection_fingerprinting`` preset.

The records it produces are written to the same ``javascript`` table with the
same schema (``operation``, ``symbol``, ``arguments``, ``value``, ``script_url``,
``func_name``, ``call_stack``, …) as legacy mode. For a given captured call the row
shape matches what legacy emits — **including the ``symbol`` string**. This is a
hard drop-in requirement: published OpenWPM fingerprinting analyses query the
``symbol`` column with exact equality (e.g.
``WHERE symbol='window.navigator.userAgent'``), so the stealth default labels each
entry with the **legacy-identical** symbol. Concretely, the default
``instrumentedName`` for the ``Navigator``, ``Screen`` and ``document`` entries is
``window.navigator``, ``window.screen`` and ``window.document`` respectively
(matching what ``clean_js_instrumentation_settings`` derives from
``collection_fingerprinting``), so e.g. ``window.navigator.userAgent``,
``window.screen.colorDepth`` and ``window.document.cookie`` are emitted
byte-for-byte under both modes. The ``TestStealthSymbolParity`` suite in
``test/test_stealth.py`` pins this: it runs one probe page through both modes and
asserts the distinct ``symbol`` sets are equal (modulo the single accepted audio
structural difference below).

.. note::

   **Argument values.** Arguments are serialized through Xrays, so an object
   argument is recorded with its own data properties only: accessor properties
   and ``toJSON`` are not evaluated, a ``Proxy`` argument is recorded as
   ``[object Proxy]``, and objects other than plain objects, arrays and typed
   arrays are recorded as their brand (``[object Storage]``). Legacy evaluates
   them. In exchange, recording runs no page code, so a
   call the page makes while another instrumented call is in progress (for
   example from a getter that the native reads) is recorded; legacy's
   re-entrancy guard drops it.

Compared to the legacy ``collection_fingerprinting`` preset (the default):

**Captured identically (same ``symbol``):** RTCPeerConnection, HTMLCanvasElement,
CanvasRenderingContext2D, Storage (``getItem``/``setItem``/…),
``window.navigator.*`` (``userAgent``, ``platform``, ``languages``, ``webdriver``,
…), ``window.screen.*`` (``colorDepth``, ``pixelDepth``),
``window.document.cookie``, ``window.document.referrer``, ``window.name``
(get/set), ``window.localStorage`` / ``window.sessionStorage`` (property get). The
own (non-inherited) properties of the audio node/context children also match
(e.g. ``AnalyserNode.frequencyBinCount``, ``AnalyserNode.getFloatFrequencyData``,
``AudioContext.close``).

**Captured additionally by stealth:** ``AudioWorkletNode`` (the modern
replacement legacy lacks); all ``Screen`` properties (legacy records only
``colorDepth``/``pixelDepth``).

**Captured by legacy only:** ``window.navigator.sendBeacon``, which the stealth
default leaves to ``http_instrument`` (see `Configuring the instrumented
surface`_).

Accepted structural differences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following are deliberate, accepted differences in *how* a capture is
recorded — not capability gaps, and immaterial for fingerprinting analysis:

- **Audio shared-prototype granularity.** Methods that live on a shared parent
  prototype (``AudioNode.connect``/``disconnect``,
  ``BaseAudioContext.createGain``/``createOscillator``/``createAnalyser``/…) are
  hooked **once** on the shared prototype under stealth, versus once per child
  interface under legacy, so their ``symbol`` label and row multiplicity differ:
  stealth records ``AudioNode.connect`` and
  ``[AudioContext|OfflineAudioContext].createGain``.
  Hooking the shared method once is a stealth requirement: redefining the same
  native accessor under several child names would mean redefining it several
  times, which is page-observable. The captured **calls** are identical, but
  the bundled default does not record which node type a shared method was
  called on (an entry with ``receiverInterfaces`` would, in the ``receiver``
  column). ``TestStealthSymbolParity`` encodes this exact
  delta (``LEGACY_ONLY_AUDIO_SYMBOLS`` / ``STEALTH_ONLY_AUDIO_SYMBOLS``) and
  asserts everything else matches.

Every ``logSettings`` field except ``recursive`` is honoured by the stealth
instrument (see `logSettings semantics`_). ``recursive`` is the one legacy
capability stealth cannot support — a stealth surface requesting it is rejected
at config-validation time (see `Limitation: recursive is unsupported`_). The
bundled default leaves the optional fields (``preventSets``, ``logFunctionGets``,
``nonExistingPropertiesToInstrument``) off, exactly like legacy's
``collection_fingerprinting`` preset; a study can enable any of them via a custom
``stealth_js_instrument_settings`` (see `Configuring the instrumented surface`_).

logSettings semantics
~~~~~~~~~~~~~~~~~~~~~~~

All ``logSettings`` fields are read by the stealth instrument
(``Extension/src/stealth/instrument.ts``) and match the legacy semantics defined
in ``Extension/src/lib/js-instruments.ts``:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Stealth behaviour
   * - ``propertiesToInstrument``
     - Named list (with ``{depth, propertyNames}``) or, when empty, every own
       property to ``depth``. ``excludedProperties``/``overwrittenProperties`` are
       filtered out on **both** paths.
   * - ``excludedProperties``
     - Skipped on the named-list path and the instrument-everything path.
   * - ``overwrittenProperties``
     - Property value overwritten on read (e.g. ``Navigator.webdriver → false``);
       accessors only, a method listed here is refused.
   * - ``logCallStack``
     - Per-object call-stack capture (page frames only; never ``moz-extension://``).
   * - ``logFunctionsAsStrings``
     - Function values serialised as their source instead of ``"FUNCTION"``.
   * - ``logFunctionGets``
     - When an instrumented getter returns a **function**, a ``get(function)`` row
       is emitted (and no plain ``get``), matching legacy.
   * - ``preventSets``
     - When the property currently holds a **function/object**, an assignment is
       logged as ``set(prevented)`` and the original setter is **not** called,
       blocking the write. Plain (string/number) values still pass through.
   * - ``recursive`` + ``depth``
     - **Unsupported under stealth.** A stealth surface with ``recursive: true``
       (and ``depth > 0``) is rejected at config-validation time with a
       ``ConfigError``; see `Limitation: recursive is unsupported`_. Use legacy
       ``js_instrument`` for configs that need it.
   * - ``nonExistingPropertiesToInstrument``
     - Names absent from the target get a synthesized, ``[native code]``-reporting
       accessor (backed by a closure variable), so a study can capture access to
       decoy non-existing property names.

**Native-arity preservation.** Instrumented functions report the **same**
``.length`` (arity) as the native function they replace (e.g.
``canvas.getContext.length === 1``). A naive wrapper forwards via ``arguments`` and
would expose ``.length === 0`` — a fingerprint. Rather than patch ``.length``
after the fact, ``makeArityForwarder`` (``instrument.ts``) *codegens* the forwarder
with exactly the native arity: it builds, via ``new Function``, a wrapper that
declares the same number of named parameters as the native function (clamped to
``[0, 256]``, and never to 0 for an over-bound arity so the page-visible
``.length`` is never mis-reported as 0). Because the forwarder genuinely declares
that many params, its own ``.length`` is the native arity, and Xray reports it
faithfully (Xray reads ``.length`` from the underlying target). The arity template
is a fixed integer count, never page-controlled input, and forwarders are cached
per arity. The ``function_arity_native detection vector (``stealth_detection.html``,
``D8b-native-fn-arity``) locks this in; legacy trips it.

**Detectability of ``nonExistingPropertiesToInstrument``.** Non-existing properties are
*intentionally* page-observable — they are bait a tracker is meant to probe.
Stealth makes them native-looking (the synthesized accessor reports
``[native code]``), so they are not identifiable as OpenWPM specifically, but a
page that *knows* a given name should not exist on a real Firefox object could
still notice the decoy. This is inherent to the technique (legacy is identical),
the names are study-chosen rather than an OpenWPM signature, and the field is
empty in the default surface — so the out-of-the-box instrument adds no such
artifact.

.. _stealth-disruptability:

Disruptability: what the off-DOM channel does and does not buy
--------------------------------------------------------------

The disruptability requirements X1–X3 (``Stealth-Requirements.rst``) test whether
a hostile page can suppress (X1) or forge (X2) records, and whether dynamically
created iframes are instrumented (X3). This section states precisely what
stealth's disruptability advantage is — and, just as importantly, what it is
**not** — so the architecture's tamper posture is argued rather than assumed.

The advantage is the off-DOM channel, not the wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stealth's disruptability win over legacy is the **off-DOM record channel**,
full stop. Legacy ships records over a page-reachable DOM
``dispatchEvent``/``eventId``, so a page can neuter ``document.dispatchEvent`` to
suppress deliveries (X1) or replay the secret event id to forge rows (X2). Stealth
sends records over the process message manager from its sandbox, which the page
cannot reach, so neither attack lands. ``TestStealthDisruption`` proves both
directions:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x1_legacy_channel_can_be_suppressed

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x1_stealth_channel_resists_suppression

The win is **not** in the wrapper. On raw wrapper-deletability stealth and legacy
are equal: both install their wrappers with ``configurable: true``, so a page can
``delete`` or ``Object.defineProperty`` over a wrapped property under either mode
and the instrument simply stops seeing it.

- Stealth installs wrappers by redefining the **native** descriptor with its
  ``value``, ``get`` or ``set`` swapped (``instrumentFunction`` and
  ``instrumentGetterSetter`` in ``instrument.ts``). Native DOM accessor/method
  descriptors are ``configurable: true``, so the installed wrapper inherits
  ``configurable: true``.
- Legacy does the same, with an explicit ``configurable: true``
  (``js-instruments.ts``).

So "stealth resists disruption, legacy does not" is true **only for the record
channel** (:doc:`Stealth-and-Legacy-JS-Instruments`). The wrapper property itself is exactly as deletable as
legacy's, and the rest of this section is about why that gap is not closed.

The damage-bounding invariant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although a page can blind a wrapped property, it **cannot reach or forge the
native** through the instrument. This is a deliberate, load-bearing property of
the design:

- The actor instruments every window global when it is created
  (``content-document-global-created``), in a **sandbox compartment, before any
  page script executes**.
- Every wrapper closes over the native captured at that point
  (``descriptor.value`` / ``get`` / ``set``), pinned as ``Function.prototype.call``
  bound to it in a second sandbox with the page's principal (``pinNative`` in
  ``instrument.ts``, ``nativePinner`` in ``OpenWPMStealthChild.sys.mjs``). The
  page-visible forwarder is a fresh ``exportFunction`` export, not the native.
- The wrapper invokes that bound ``call`` with the sandbox's ``Reflect.apply``
  and never passes the native to page code, so replacing a page builtin does
  not expose it (the ``hooks`` section of ``TestStealthNativeParity``).

The page therefore has **no reachable handle to the captured native** of the
window it runs in. A tamper
can blind a property (delete/redefine the wrapper) — a data-quality loss for that
property — but it cannot recover the native to call it invisibly, cannot forge a
record into the off-DOM channel, and cannot substitute a function the instrument
will mistake for native. That bound is the honest "floor" of the in-compartment
design: staying undetectable means the wrapper is deletable, but the native and
the channel are not reachable.

Why in-compartment wrapper lockdown is rejected
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The reason the wrapper is left deletable is **detectability**: every move that
would harden the wrapper deviates from the native descriptor shape, and that
deviation is itself a fingerprint. A real Firefox method is
``configurable: true, writable: true, enumerable: false``; a real accessor is
``configurable: true``. A page can read these with
``Object.getOwnPropertyDescriptor``, so any deviation is page-observable. Each
prevention technique and why it is rejected:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Technique
     - Effect on disruptability
     - Why rejected
   * - ``configurable: false`` on the wrapper
     - Closes the biggest gap — the page can no longer ``delete``/redefine the
       wrapper.
     - **Detectability (high).** Native DOM props are ``configurable: true``; a
       ``getOwnPropertyDescriptor(...).configurable === false`` probe instantly
       fingerprints OpenWPM. The defense becomes the tell.
   * - ``writable: false`` on method wrappers
     - Partial — blocks ``obj.method = …`` reassignment, but not ``delete`` /
       ``defineProperty``.
     - **Detectability (high).** Native methods are ``writable: true``; the
       descriptor probe detects the deviation.
   * - ``Object.freeze`` / ``seal`` / ``preventExtensions`` on the prototype
     - Partial — blocks adding/removing properties on a frozen prototype.
     - **Detectability + breakage.** A frozen native prototype is anomalous and
       probeable, and freezing a shared prototype perturbs legitimate page
       behaviour.
   * - Heartbeat / ``setInterval`` re-install of deleted wrappers
     - Partial — would re-cover a deleted wrapper on the next tick, but races
       (calls between delete and re-install are lost).
     - **Detectability (medium-high) + complexity.** A periodic timer plus
       repeated ``defineProperty`` churn on native prototypes is anomalous and
       probeable; re-running the wrapper changes its identity, detectable via
       ``===`` caching.
   * - ``MutationObserver`` self-heal of tampered wrappers
     - None — ``MutationObserver`` fires on **DOM** mutations, never on a JS
       property ``delete``/redefine of a prototype accessor. Wrong tool.
     - N/A — DOM observation cannot detect prototype-property tampering.
   * - ``Proxy`` invariant traps over the wrapper
     - Marginal — a ``Proxy`` can trap ``defineProperty``/``deleteProperty`` only
       on an object you fully own; you cannot make the page's native prototype a
       ``Proxy`` without replacing the prototype.
     - **Detectability (high) + breakage.** Replacing a native prototype is
       massively detectable and breaks identity; on the wrapper function it buys
       nothing against property deletion.

The conclusion is that there is **no free lunch on prevention**: every wrapper
hardening move trades a disruptability gain for a detectability tell, and for a
stealth instrument detectability is the dominant constraint. The already-strong
parts — closure-private natives captured before any page script, and no
page-reachable handle to the native (`The damage-bounding invariant`_) — are kept;
the lockdown moves are not adopted.

Future work: tamper telemetry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The one improvement that does **not** pay a detectability tax is **tamper
telemetry**: a privileged-side (Xray, page-untouching) passive check that a
wrapped descriptor still points at our forwarder, with any divergence reported
**off-DOM** via the existing record channel. Because the check lives
entirely on the privileged side and mutates nothing on the page, it adds no
detection surface.

Telemetry does **not** prevent tampering — a page can still delete a wrapper. What
it changes is that a silent blind-spot becomes a **measurable data-quality
signal**: a dataset can record that property ``X`` on host ``Y`` was tampered with,
rather than silently missing those calls. For a measurement tool that is the right
trade — it improves the *interpretability* of the data without the detectability
cost that prevention would incur. This is recorded as future work; nothing like it
ships today.

Test coverage
-------------

:doc:`Stealth-Validation` maps every way the instrument could taint a study to
the test that guards it. ``test/test_stealth.py`` is requirement-driven: each
test maps to a numbered
requirement in ``docs/developers/Stealth-Requirements.rst``. See that document for
the full detectability (D1–D12), disruptability (X1–X3), attribution (A1) and
configurability (C1) matrices and the per-requirement test names. The
detectability vectors are asserted in both directions — stealth must pass, legacy
(as a control) must trip the reliably-detected subset:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDetectability.test_stealth_undetectable

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDetectability.test_legacy_detectable

In summary:

- **Detectability** — ``stealth_detection.html`` exercises the 31 parametrized
  vectors (D1, D2×3, D3, D4, D5, D6, D7, D8, D8b, D8c, D9, D10×16, D11, D12);
  ``TestStealthDetectability`` asserts stealth passes every vector and that legacy
  trips the reliably-detected subset (D1, D2×3, D4, D5, D8, D8b) as a control.
  The others are asserted only in the stealth direction, because legacy's
  behaviour on them is environment- or configuration-dependent or it does not
  touch the probed member either.
- ``logSettings`` **fidelity** — ``TestStealthLogSettings`` proves the stealth
  instrument honours ``preventSets`` (logs ``set(prevented)`` and blocks the
  write), ``logFunctionGets`` (emits ``get(function)``), and
  ``nonExistingPropertiesToInstrument`` (synthesized accessor for a non-existing
  property), each with a native-looking / undetectability check where the target
  is a native object
  (pages ``stealth_prevent_sets.html``, ``stealth_non_existing_props.html``).
- ``recursive`` **rejection** — ``TestStealthRecursiveRejected`` proves a stealth
  surface with ``recursive: true`` is rejected at config-validation time with a
  ``ConfigError`` (it is unsupported; see `Limitation: recursive is
  unsupported`_). These tests run config-only (``pyonly``) — no browser.
- **Disruptability** — ``TestStealthDisruption`` runs the X1 (suppression), X2
  (forgery) and X3 (dynamic iframe) attack pages both ways: legacy is shown to
  lose/accept records or miss the parent-context attribution, stealth to resist
  and instrument the dynamic frame.
- **Attribution** — the A1 test asserts stealth records name the page script and
  carry a ``call_stack`` free of ``moz-extension://`` frames.
- **Configurability** — ``TestStealthConfigurability`` proves a custom surface
  replaces the default (via a distinctive ``instrumentedName``) and stays
  undetectable.

Known limitations / future work
-------------------------------

Limitation: ``recursive`` is unsupported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``recursive`` instrumentation is the **one legacy ``logSettings`` capability the
stealth instrument cannot support**. A stealth surface that sets
``logSettings.recursive: true`` (with ``depth > 0``) is rejected at
config-validation time with a ``ConfigError`` (``openwpm/config.py``,
``validate_browser_params``). The actionable message points the user at legacy ``js_instrument``,
which still supports ``recursive`` because it runs in the page's own compartment.

**Why stealth refuses it.** Recursion requires instrumenting the
``Object``/``Array`` instances **returned by an instrumented getter**. Those
instances are plain containers with no global interface prototype to hook, so
the only remaining place to install an accessor is the returned page instance
itself — a **page-observable own-property mutation that any script can detect**.
Stealth **deliberately refuses** to do this rather than give itself away, and
rejects the config instead (``openwpm/config.py``, ``validate_browser_params``).

This is a design refusal, **not** a platform prohibition: nothing in Firefox's
Xray machinery stops the define. The ceiling is a choice with a stated reason.

Undetectability is the property stealth exists to provide, and mutating the
page's own object graph is incompatible with it. Legacy can do this **only**
because it executes in the page compartment (where it is, by the same token,
detectable).
Everything else legacy can do — prototype hooks, native-instance accessors,
non-existing properties (``nonExistingPropertiesToInstrument``), ``preventSets``, ``logFunctionGets``,
``logCallStack`` — stealth supports. Configs that need ``recursive`` must stay on
``js_instrument``.

Mechanical expansion: ``recursive`` → flat stealth config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although a ``recursive`` stealth surface is *rejected*, the recursion it asks for
can be expanded ahead of time into a **flat, non-recursive** stealth config that
covers the bulk of the legacy recursive surface (the per-node own-prototype
names), reporting the inherent gaps explicitly rather than dropping them silently
(see `Coverage is not loss-free`_). ``openwpm/utilities/js_settings_migrator.py`` does
this with a browser-based sweep: given a researcher's legacy
``js_instrument_settings`` (including ``recursive`` entries), it launches a
lightweight Firefox and replays the **exact** legacy descent (``instrumentObject``
in ``Extension/src/lib/js-instruments.ts``) over the live object graph, then emits
one flat stealth entry per reached node (``object`` = the node's
``constructor.name``, the bare global prototype stealth hooks; ``instrumentedName``
= the legacy symbol path; ``recursive`` forced off).

.. code-block:: bash

   python -m openwpm.utilities.js_settings_migrator YOUR_LEGACY_CONFIG.json \
       --output stealth_config.json

``YOUR_LEGACY_CONFIG.json`` holds the same settings list in the legacy
``js_instrument_settings`` form; the generated list is ready to assign to
``browser_params.stealth_js_instrument_settings``. So the actionable answer to the
recursive ``ConfigError`` is "run this script", not "go back to legacy".

Coverage is not loss-free
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The swept stealth config does **not** reproduce the legacy recursive surface
exactly. The mismatch is two-directional, and both directions are surfaced
explicitly rather than claimed away:

- **Stealth set B is a strict superset of legacy set A for object-valued
  properties.** Under recursion legacy *suppresses* the plain ``get`` of an
  object-valued property while it descends into it (see ``instrumentObject`` in
  ``Extension/src/lib/js-instruments.ts`` — the recursion branch returns the
  recursed child without emitting that property's own ``get`` row). The flat
  stealth entry has no recursion to suppress, so it logs that ``get``. So for those
  members stealth records **more** than legacy, not fewer. The parity test asserts
  B ⊇ (A − reported gaps); it does **not** claim the two sets are equal.

- **Legacy covers names stealth does not.** These are the names legacy reaches
  that stealth's flat hooks cannot, all returned as ``UntranslatedEntry`` objects
  (the second element of the ``legacy_settings_to_stealth`` return tuple) and
  logged — never dropped silently, and any of them makes the CLI exit non-zero
  so an automated pipeline cannot mistake an incomplete translation for a
  clean one. (``UntranslatedEntry`` is the code-level type name.) Four
  classes:

  1. **Untranslatable node** — a node whose ``constructor.name`` is
     ``Object``/``Array``/falsy (e.g. ``navigator.languages``, a plain ``Array``)
     has **no global interface prototype** for stealth to hook, so the whole node
     cannot be expressed as a stealth entry. Same plain-node / shared-prototype
     granularity class as the audio structural difference above.
  2. **Universal-prototype inherited member, or inherited non-method member** —
     legacy's ``Object.getPropertyNames(instance)`` covers the instance's own
     names **plus the entire prototype chain** to ``null``. The emitted leaf
     stealth entry uses ``depth: 0``, so ``getPropertyNamesPerDepth(proto, 0)``
     covers only the **leaf** interface prototype's **own** names. Two sub-cases
     of the inherited remainder are not translated: members owned by a
     **universal** prototype (``Object.prototype``/``Function.prototype``/
     ``Array.prototype`` — ``toString``, ``valueOf``, …; instrumenting them would
     fire on virtually every receiver), and **inherited accessors / data members**
     (e.g. ``Document.prototype.URL``), whose receiver cannot be filtered at call
     time the way a method's can. Inherited **methods** owned by a real interface
     prototype are **not** in this class — see `Interface-attributed
     shared-prototype capture`_.
  3. **Resolution failure** — a legacy ``object`` string that does not ``eval`` to
     a live node.
  4. **Unwrapped by design** — a member the stealth default leaves unwrapped
     (``navigator.sendBeacon``), left out of the translated entry and reported
     with the guidance in `Configuring the instrumented surface`_.

Interface-attributed shared-prototype capture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An inherited **method** owned by a real global interface prototype — e.g.
``addEventListener`` on ``EventTarget.prototype``, reached via a DOM element /
``navigator.permissions`` / ``XMLHttpRequest`` / ``window.document`` / … — is
**captured**, not lost. For each such ``(owner interface, method)`` the sweep
emits a single shared-prototype stealth entry that hooks the method **once** on
the owner's prototype and carries a ``receiverInterfaces`` field — the set of leaf
interface names that reached it:

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

At call time the stealth instrument (``logCall`` / ``getReceiverInterfaceName`` in
``Extension/src/stealth/instrument.ts``) reads the **receiver's interface name**
from ``this``. ``this`` is an Xray view of the page object as seen from the
instrument's sandbox compartment; the Xray presents a clean **native** view
and hides page-side modifications, so the read
(``Object.getPrototypeOf(this).constructor.name``, falling back to
``this.constructor.name``) resolves to the genuine interface name **even when the
page has redefined** ``constructor`` on the instance or its prototype — verified
against ``js/xpconnect/wrappers/XrayWrapper.cpp`` and measured in a real Firefox
run. The read is pure privileged-side reflection: it defines nothing on the page
and triggers no page-side getter, so it adds **no** new detection surface.

The instrument then:

- **filters sandbox-side** — the call is recorded **only** if the receiver
  interface is in ``receiverInterfaces``; calls on other interfaces are dropped
  before any record is emitted (no site-wide flood, nothing to discard in
  post-processing), and
- **attributes by interface in a dedicated column** — the recorded ``symbol`` stays
  the **static** shared-prototype method (e.g. ``EventTarget.addEventListener``),
  and the concrete receiver interface (e.g. ``HTMLDivElement``) is written to a
  dedicated nullable ``receiver`` column on the ``javascript`` table.
  Post-processing therefore filters by ``receiver`` (e.g.
  ``WHERE symbol='EventTarget.addEventListener' AND receiver='HTMLDivElement'``)
  rather than parsing it out of ``symbol``.

Attribution is **interface-level**: it does not (and is not meant to) distinguish
two instances of the same interface — that is exactly the granularity researchers
filter by in post-processing. When an entry has **no** ``receiverInterfaces``
field, behaviour is unchanged: the method is recorded under its static symbol, the
``receiver`` column is **NULL**, and every call is emitted. The ``receiver`` column
is purely additive — ordinary instrumentation and value gets/sets always leave it
NULL, so existing queries and rows are unaffected. The
``TestStealthSharedPrototypeCapture`` and ``TestStealthSweepSharedPrototype`` suites
in ``test/test_stealth.py`` lock in the capture, the discriminating filter, and the
regression (absent field → unchanged).

The ``TestStealthRecursiveSweepParity`` suite proves the guarantee: it runs a
``recursive`` config under legacy (symbol set A), sweeps it, runs the generated
flat config under stealth (symbol set B), asserts B covers A modulo the reported
gaps, **and** asserts that any legacy symbol absent from B is reported (no silent
drop). A dedicated test exercises a universal-prototype inherited member
(``navigator.permissions.toString``, inherited from ``Object.prototype``)
end-to-end to lock the reporting in place, while ``TestStealthSweepSharedPrototype``
proves an inherited **method** owned by a real interface
(``EventTarget.addEventListener`` reached via ``window.document``) becomes an
interface-attributed shared-prototype entry instead.

Opt-in: capturing universal-prototype methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default the sweep keeps inherited methods owned by a **universal** prototype
(``Object.prototype`` / ``Function.prototype`` / ``Array.prototype`` — ``toString``,
``valueOf``, ``hasOwnProperty``, …) untranslated (class 2 above). That default is
deliberate: virtually every object on a page inherits from these prototypes, so
hooking ``Object.prototype.toString`` fires the wrapper on **every** object's
``toString()`` call page-wide — a very high-overhead, very-high-volume capture for
essentially **zero tracking signal**. Legacy ``recursive`` *did* hook them (it
walked the full prototype chain), so a researcher who needs strict
legacy-``recursive`` parity can opt back in:

- **Library:** pass ``capture_universal_prototype_members=True`` to
  ``legacy_settings_to_stealth(...)``.
- **CLI:** add the ``--capture-universal-members`` flag.

When enabled, the universal **methods** are routed into the **same**
interface-attributed shared-prototype mechanism as real interfaces: the sweep
emits a single consolidated ``{object: "Object" | "Function" | "Array", depth: 0,
…}`` entry whose ``propertiesToInstrument`` lists every reached universal method and
whose ``receiverInterfaces`` covers all leaf interfaces that reached them (e.g.
``Navigator``, ``Permissions``, …). The stealth instrument resolves
``{object: "Object"}`` to the page realm's ``Object.prototype`` via
``wrappedJSObject["Object"].prototype`` — exactly the resolution used for real
interfaces — so **no extension change is required**. At call time the same
receiver-interface filter applies, so a record is emitted only for the configured
leaf interfaces (not for every object on the page).

.. warning::

   This wraps base-prototype methods that fire on essentially every object — you
   are wrapping every ``toString``. It is rarely what you want; enable it **only**
   for strict legacy-``recursive`` parity. Non-method universal members (accessors
   such as ``__proto__``) stay untranslated regardless of the flag, because the
   receiver-interface filter only applies to methods at call time. With the flag
   **off**, behaviour is unchanged (universal methods untranslated, no
   ``Object``/``Array`` entry emitted). ``TestStealthSweepUniversalPrototypeCapture``
   in ``test/test_stealth.py`` locks in both the flag-off default and the flag-on
   capture.

Other coverage notes
~~~~~~~~~~~~~~~~~~~~~~

- **X3 (dynamic iframes).** The actor instruments the initial ``about:blank``
  document of a dynamically-created iframe that is navigating, where no
  content script runs, when its window global is created; a paired regression
  test ships (``test_x3_*`` in ``test/test_stealth.py``, page
  ``stealth_disruption_iframe.html``). Stealth records an in-iframe
  ``toDataURL`` there under that document (``about:blank``) and the frame's
  ``frame_id``; legacy does not record it. ``TestStealthFirstLoad`` covers the
  same for popups and for frames reached only through ``window[n]``. See
  ``Stealth-Requirements.rst`` for the attribution rule.
- **Out of scope** (environment fingerprints, not instrumentation artifacts):
  screen/window position, font enumeration, WebGL deviations, timezone. Also out
  of scope: silent JS delivery via non-``.js`` MIME/extension, which concerns the
  HTTP instrument rather than the JS instrument.

Design decisions
----------------

- :doc:`Stealth-and-Legacy-JS-Instruments` — why legacy is kept although
  stealth supersedes it on detectability and disruptability: the two narrow
  capabilities only legacy has (plain-object recursion, interface naming of
  inherited members), and what each instrument records differently.
