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
  (``window.jsInstruments``, ``getInstrumentJS``), ``navigator.webdriver``,
  extension stack frames — is eliminated. ``toString`` returns ``[native code]``
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

Consequences
------------

- **Detection surface is a property of the** *legacy* **instrument, not
  stealth.** A stealth-only run exposes nothing to detect — there is no per-API
  detectability to enumerate. Detection only enters the picture when a run
  includes legacy (today, an exclusive legacy run; later, a mixed run if
  mutual-exclusion relaxes). Legacy's detection surface splits two ways: a
  **per-API surface** that is inherent to wrapping in the page compartment and
  **cannot** be removed, and a **global footprint** (added globals,
  content-script artifacts) that **might** be hidden better (the legacy-footprint
  follow-up below). Guidance must scope the detection discussion to legacy and
  keep these two apart.
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
