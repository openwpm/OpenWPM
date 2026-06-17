ADR: Retain the legacy JS instrument as a narrow capture fallback to stealth
============================================================================

:Status: Accepted
:Date: 2026-06-15
:Context PR: stealth JS instrument (``feat/stealth-js-instrument-v2``)

Context
-------

OpenWPM has two JavaScript instruments: the **legacy** instrument
(``js_instrument``) and the **stealth** instrument (``stealth_js_instrument``).
They are **mutually exclusive** today (a ``ConfigError`` is raised if both are
enabled).

Stealth improves on legacy along two **independent** axes — they are separate
mechanisms with separate root causes, not a dependency chain:

- **Detectability.** Every artifact the reliability paper (Krumnow, Jonker &
  Karsch, arXiv:2205.08890, 2022) names — ``toString`` returning the wrapper
  body, mismatched function arity, prototype pollution, leaked globals
  (``window.jsInstruments``, ``getInstrumentJS``), ``navigator.webdriver`` — is
  eliminated. ``toString`` returns ``[native code]``
  via a native passthrough; arity is preserved per-target from
  ``originalFn.length``; ``Window.prototype`` accessors such as ``window.name``
  are captured by redefining the descriptor on the prototype where the browser
  natively defines it, adding no own property to the ``window`` instance.
  Detectability is a property of the instrument's **footprint** — what it leaves
  visible in the page.
- **Tamper-resilience.** The two tamper threats the paper names — **disruption**
  (suppressing record delivery) and **false-data** (forging records) — are
  countered by *where the record channel lives*. Legacy ships records over a
  page-reachable DOM ``dispatchEvent``; stealth delivers them through the
  privileged ``browser.runtime`` channel, which has no page-reachable handle.
  This is an independent mechanism: it would hold even for a hypothetically
  *detectable* instrument that still used the off-DOM channel, and conversely an
  undetectable instrument on the DOM channel would still be disruptable. See
  `Tamper-resilience`_ below.

Legacy is therefore both more detectable (it lives in the page compartment)
**and** more disruptable (its record channel is page-reachable). The two are
distinct shortcomings; stealth addresses each on its own terms.

This raises the decision this ADR records: **once stealth subsumes legacy, why
keep legacy at all rather than delete it?**

Decision
--------

**Retain legacy as a narrow, opt-in capture fallback — do not delete it, and do
not treat it as a co-equal peer.**

Two genuine capability gaps remain where legacy can record something stealth
cannot, and they are the entire reason legacy survives:

1. **Recursion into plain (non-interface) objects.** Instrumenting an arbitrary
   ``Object``/``Array`` instance returned by an instrumented getter has no global
   interface prototype to hook, so capturing it would require defining accessors
   directly on that returned page instance — a page-observable own-property
   mutation that any script can detect. Stealth **deliberately refuses** to do
   this rather than give itself away, and rejects ``logSettings.recursive`` at
   config-validation time with a ``ConfigError``. The ceiling is precisely
   "recursion into plain containers" — most recursively-reached nodes are
   platform-typed (``Navigator``, ``Screen``, audio interfaces) and the sweep
   utility below translates them cleanly; only bare ``Object``/``Array`` nodes
   (e.g. ``navigator.languages``) have no global prototype to hook.

2. **Per-instance attribution for shared-prototype methods.** Legacy wraps a
   method *on the instance*, attributing a call to the specific object it was
   invoked on. Stealth redefines on the interface prototype (the only place it
   can stay native) and attributes such calls *by interface* (recorded in the
   ``receiver`` column). Every call is still recorded; only per-instance
   granularity is lost.

A researcher reaches for legacy only by accepting both of legacy's independent
shortcomings — detectability *and* a page-reachable record channel — in exchange
for one of these two capability gaps. That is a deliberate opt-in to a superseded
technology, not a routine choice — and it is the sole justification for keeping
legacy in the tree.

**Why retain rather than delete.** These two gaps are real measurement
capabilities with no stealth equivalent. Deleting legacy would remove them
outright; retaining it behind mutual-exclusion preserves them at zero cost to the
stealth default (a study that does not opt into legacy never pays for it). The
cost of retention is maintenance of dead-for-most-users code; the cost of
deletion is permanent loss of two narrow but genuine capture modes. We choose
retention until those gaps are either closed in stealth or shown to be unused in
practice.

**Ergonomics are not a reason to keep legacy.** Stealth uses a distinct settings
convention (bare global names, explicit ``{depth, propertyNames}``).
``openwpm/utilities/js_settings_migrator.py`` translates a legacy config into an
equivalent flat stealth config, replaying the legacy descent over a live object
graph and reporting any untranslatable plain-object nodes rather than dropping
them silently. The captured ``symbol`` column is byte-identical to legacy, so
downstream analyses querying ``symbol`` are unaffected by the switch. Translation
is "run one script", not a reason to stay on legacy.

Tamper-resilience
-----------------

The reliability paper names two tamper threats: **disruption** (the page
suppresses record delivery so calls go unrecorded) and **false-data** (the page
forges records to pollute the dataset). The PR's disruptability requirements
X1–X3 (:doc:`../Stealth-Requirements`) test these directly. Both are properties
of the **record channel**, not of the wrappers, and they do not depend on the
page first defeating detection — a page can target a known instrumentation
channel even when it cannot tell which automation framework installed it.

The asymmetry favors stealth on the channel:

- **Legacy's record channel rides the DOM.** A page-reachable
  ``dispatchEvent``/``eventId`` can be neutered to suppress deliveries (X1) or
  replayed to forge rows (X2).
- **Stealth's record channel is off-DOM.** Records go through the privileged
  ``browser.runtime`` channel, which the page cannot reach to drop or forge. This
  is the entirety of stealth's tamper-resilience win — it is independent of
  detectability and orthogonal to how the *wrappers* are installed.

Note the scope of this win precisely: it is the **delivery channel**, not the
wrapper. On raw wrapper-deletability the two modes are equal — both install
wrappers with ``configurable: true``, so a page can ``delete`` or redefine a
wrapped property under either mode and blind that property. The detailed
treatment of wrapper tamper-resistance, why in-compartment lockdown is rejected,
and what bounds the damage lives in
:ref:`Stealth-Instrumentation <stealth-disruptability>` ("Disruptability: what
the off-DOM channel does and does not buy"). The ADR's claim is the narrow, true
one: stealth's record *channel* cannot be suppressed or forged from the page;
legacy's can.

Open question (gates compose viability)
---------------------------------------

Is legacy detectable **only via the APIs it wraps**, or does its injection
**footprint** (added globals, content-script artifacts, timing signatures) leak
independently? The long-term goal is to relax blanket mutual-exclusion to an
*overlap check* (error only if a single property is claimed by both instruments),
letting a study run stealth for most APIs and legacy for the remaining ones in
the same browser. That only yields a stealthy browser if legacy's detectability
is confined to its wrapped properties. If the footprint itself leaks, the work is
not "partition the APIs" but "make legacy's footprint invisible" — a larger job.
Tracked as issue `#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_.

Legacy's detectability ceiling is architectural
-----------------------------------------------

The per-API surface above is not merely "hard to hide" — for a class of
artifacts it is **structurally** un-hideable in legacy's architecture (a
plain-JS wrapper injected into the *page* compartment), and that ceiling is the
affirmative case for stealth carrying its extra machinery. The high-value
page-world tells the reliability paper names were probed empirically; they split
into removable and structurally-fixed:

- **Cheaply fixable, no tradeoff.** Wrapper function **arity** (``fn.length``)
  and **name** (``fn.name``) can be copied from the native target onto the
  wrapper so they match native exactly, at zero capture cost (verified
  before/after on a live ``CanvasRenderingContext2D.prototype.getImageData``;
  implemented for legacy in the (open draft) `#1210
  <https://github.com/openwpm/OpenWPM/pull/1210>`_). These tells are removable,
  and legacy should remove them — so they are *not* part of the ceiling.
- **Structurally un-hideable — wall 1: cross-realm (**``toString``**).** Making a
  wrapped function's ``toString`` return ``[native code]`` requires patching
  ``Function.prototype.toString``. Legacy lives in the page compartment, so it can
  patch only the **main realm**: a page reads the un-patched original straight out
  of any fresh realm —
  ``iframe.contentWindow.Function.prototype.toString.call(fn)`` returns the
  wrapper body (measured, not theorised). Closing that means re-patching every
  realm as it is created — a treadmill — **and** permanently mutating a core
  intrinsic, a larger and more detectable footprint than the single leak it
  removes. The fix is net-negative, so the leak stands.
- **Removable but costly — prototype pollution (an implementation choice, not a
  wall).** Legacy captures whole-interface **inherited** members by flattening the
  prototype chain — copying ancestor members down as own properties of the leaf
  prototype. That flattening *is* the page-observable footprint
  (``getOwnPropertyNames``/``hasOwnProperty`` see the materialised members;
  measured as +11 own props on ``CanvasRenderingContext2D.prototype``). But the
  pollution exists only because legacy *chooses* to hook every member on the leaf
  prototype for cheap per-leaf attribution — it is not forced by the page-world
  architecture. The receiver/interface-attribution mechanism stealth already ships
  is privilege-free reflection on ``this``
  (``Object.getPrototypeOf(this).constructor.name`` plus an ``includes`` filter —
  no ``browser.*``, no Xray, no ``exportFunction``), so it ports to a page-world
  wrapper unchanged. A legacy wrapper could hook each inherited member **once on
  its owning prototype** and attribute by reading ``this``, capturing the
  inherited member with zero own-property pollution and removing the vector. So
  "cleanliness and inherited-member capture are the same lever" holds only for
  legacy's *current* leaf-hooking design, not for a plain-JS wrapper in general:
  this is **not yet done**, not architecturally walled. The costs of porting it
  are real — and are why it is retained rather than free: attribution drops from
  per-instance to **interface-level** (lost granularity); without Xray the page can
  redefine ``constructor``/``constructor.name`` to spoof or suppress the attributed
  interface (page-spoofable attribution, an integrity downgrade); the captured-data
  layout changes (a ``receiver`` column / consolidated shared-prototype entries
  instead of flat per-leaf rows), a regression for existing analysis scripts that
  is remediable by pre-/post-processing; and it is real engineering — re-architecting
  legacy from "flatten + hook-leaf" to "resolve owning prototype + hook-once +
  filter" and reworking the 11-of-14 ``collection_fingerprinting`` entries.

**The genuine structural ceiling is wall 1 alone.** Cross-realm ``toString`` has
no privilege-free page-world fix: a plain-JS wrapper can patch only the main
realm, so the un-patched intrinsic is always one fresh realm away. That is the
irreducible tell, and it is exactly what stealth's genuine ``moz-extension://``
content-script world with ``exportFunction``/Xray removes — stealth's
**fingerprinting instrument** (the ``exportFunction``-based capture surface:
navigator/canvas/storage/RTC/``window.name``/``document.cookie``) never mutates
a page intrinsic, so on that surface there is no realm treadmill and no
``toString``/intrinsic footprint to leak. Stealth also avoids the prototype-pollution footprint for
free, because Xray reflection lets it attribute interface-level calls without
own-property materialisation — but that is the pollution vector *being cheap to
avoid*, not a second structural wall: legacy could close it too (at the
data-layout and attribution cost above) without any privilege. The extra
machinery buys legacy out of one genuine **structural** ceiling, not merely a
longer round of cat-and-mouse — and that is why, despite its ergonomic
clunkiness, stealth earns its keep.

**Limitation — the inherited frame-protection layer is the exception.** The
"never mutates a page intrinsic" claim above is scoped to the fingerprinting
instrument. Stealth also ships an inherited frame-protection / DOM-hook layer
(``Extension/src/stealth/index.ts``, derived from CanvasBlocker — hooking
``appendChild``/``document.write``/``window.open`` and iframe ``contentWindow``
access), and that layer **does** carry a Wall-1 footprint of its own. To mask
its page-facing ``Proxy`` objects it patches the main-realm
``Function.prototype.toString``, and to keep newly created same-origin frames
instrumented it runs exactly the **realm treadmill** this section attributes to
legacy — eagerly re-instrumenting each new frame/realm. So for this layer the two
things the fingerprinting instrument avoids — main-realm intrinsic mutation and a
realm treadmill — are both present, a ``toString``/intrinsic footprint of the
same Wall-1 class. Its cross-realm undetectability is bounded empirically by the
new ``D10-fp-*`` detection-vector tests (``test/test_stealth.py`` /
``test/test_pages/stealth_detection.html``), **not** by a structural guarantee:
it is not proven safe against an escape realm the treadmill misses. This is an
honest, test-bounded limitation — a known open edge of the same Wall-1 class, not
a closed wall.

Scope the claim honestly: this is empirical on the high-value vectors
(``toString``, prototype pollution, arity, name), not a closed-form impossibility
proof for every conceivable tell. The one wall that genuinely generalises is
main-realm-only intrinsic patching (``toString``): it is a property of any
"page-world plain-JS wrapper", not of the specific APIs probed, so it stands
rather than being an artifact of which vectors were tested. Prototype pollution
does *not* generalise into a wall — it is an implementation choice legacy can drop
at a data-layout and attribution cost, in the same removable category as arity and
name (only costlier), not a structural ceiling.

Consequences
------------

- **Detection surface is a property of the** *legacy* **instrument, not
  stealth.** A stealth-only run exposes nothing to detect — there is no per-API
  detectability to enumerate. Detection only enters the picture when a run
  includes legacy (today, an exclusive legacy run; later, a mixed run if
  mutual-exclusion relaxes). Legacy's detection surface splits two ways: a
  **per-API surface** inherent to wrapping in the page compartment, and a
  **global footprint** (added globals, content-script artifacts) that **might**
  be hidden better (the legacy-footprint follow-up below). The per-API surface is
  itself non-uniform — see `Legacy's detectability ceiling is architectural`_:
  some tells (arity, name) are cheaply removable, ``toString`` (cross-realm
  intrinsic patching) is **structurally** un-hideable in this architecture, and
  prototype pollution is removable but costly — an implementation choice legacy
  could drop at a data-layout and attribution cost, not a second structural wall.
  Guidance must scope the detection discussion to legacy and keep these axes apart.
- **Both instruments stay maintained**, but legacy's justification is honestly
  narrow: the two capability gaps, *not* a broad class of APIs stealth cannot
  reach, and *not* tamper-resilience (an independent stealth advantage on the
  record channel).
- The mutual-exclusion default can later relax to overlap-validation, pending the
  open question above.
- A **shared base** (webdriver hiding, native ``toString``/arity) is worth
  extracting from stealth so even a detectable legacy run stops failing the easy
  detection checks at zero capture cost — e.g. ``navigator.webdriver=false``
  decouples the automation fingerprint from the instrumentation fingerprint. The
  off-DOM **record channel** could likewise be back-ported to legacy
  independently, since tamper-resilience is a channel property, not a consequence
  of undetectability — see the legacy-comms-hardening follow-up.

Follow-ups
----------

1. **Open — legacy footprint:** verify whether legacy's detectability is confined
   to its wrapped APIs or leaks via its injection footprint (the open question
   above). Issue `#1187 <https://github.com/openwpm/OpenWPM/issues/1187>`_.
2. Relax the config from mutual-exclusion to overlap-validation.
3. Extract the shared base layer (webdriver/``toString``/arity) from stealth so
   legacy can use it.
4. **Harden the legacy record channel** independently of stealth — back-port the
   off-DOM ``browser.runtime`` delivery (or an equivalent page-unreachable
   channel) to the legacy instrument so a detectable legacy run is no longer
   *also* disruptable. This is a separate change from #1154, tracked as a
   follow-up; it underscores that tamper-resilience is a channel property that can
   be added to legacy without making legacy undetectable.

Deliverables shipped in this PR
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Symbol parity:** the ``symbol`` column is byte-identical to legacy
  (``TestStealthSymbolParity``), modulo one documented audio shared-prototype
  granularity delta.
- **``logFunctionsAsStrings`` parity** and the rest of the ``logSettings``
  semantics: all nine ``logSettings`` fields are honoured **except**
  ``recursive``.
- **``recursive`` ConfigError + sweep escape-hatch:** a recursive stealth surface
  is rejected at config-validation time with an actionable message, and
  ``openwpm/utilities/js_settings_migrator.py`` expands it into an equivalent flat
  stealth config (reporting untranslatable plain-object nodes rather than dropping
  them).
