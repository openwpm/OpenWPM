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

The two differ in which world they run their wrappers in, so the argument below
turns on Gecko's script-security model. Legacy injects a wrapper into the page
world; stealth stays in the extension's `content script
<https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts>`_
compartment and reaches the page through `Xray vision
<https://firefox-source-docs.mozilla.org/dom/scriptSecurity/xray_vision.html>`_,
exposing only what it chooses to via `exportFunction
<https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Sharing_objects_with_page_scripts>`_.
Two Xray properties are load-bearing here: a script holding an Xray sees the
native object rather than any page redefinition, and properties the extension
adds on its side are expandos the page cannot observe.

Stealth improves on legacy along two **independent** axes — they are separate
mechanisms with separate root causes, not a dependency chain:

- **Detectability.** Every artifact the reliability paper (Krumnow, Jonker &
  Karsch, `arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_, 2022) names — ``toString`` returning the wrapper
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

2. **Attribution naming for inherited members.** Legacy's flattening descent
   copies an inherited member onto the *first* prototype in the chain, so a call
   is attributed to the interface the member was reached through rather than to
   the one that owns it. Stealth redefines on the interface prototype (the only
   place it can stay native) and attributes such calls *by interface*, recorded
   in the ``receiver`` column. Every call is still recorded under either
   instrument; what differs is which interface name the call is filed under for
   inherited members.

   Both instruments hook the same object. Legacy resolves
   ``window['X'].prototype`` (``openwpm/js_instrumentation.py:125``) and defines
   there (``Extension/src/lib/js-instruments.ts:587``), which is exactly where
   stealth hooks; the only instance mutation legacy performs is value shadowing
   on the *set* path (``js-instruments.ts:700``), which installs no
   instrumentation. Nor is there per-instance granularity in the record to lose:
   ``logCall`` (``js-instruments.ts:332``) never serializes ``this``, so the
   receiving object never reaches the ``javascript`` table. The gap is therefore
   narrower than a per-instance/per-interface framing would suggest.

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

**Migrating a settings file.** Stealth uses a different settings convention to
legacy: bare global names and explicit ``{depth, propertyNames}`` entries.
``openwpm/utilities/js_settings_migrator.py`` translates an existing legacy
config into the equivalent stealth one. It replays the legacy descent over a
live object graph rather than rewriting the file textually, so the result
reflects what legacy would actually have instrumented, and it reports any
plain-object node it cannot translate instead of dropping it — which is also how
a study finds out whether it depends on the recursion gap above. The captured
``symbol`` values are unchanged, so existing analyses that query ``symbol``
continue to work against data collected either way.

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

Why the instruments stay mutually exclusive
-------------------------------------------

The long-term goal was to relax blanket mutual exclusion to an *overlap check*
(error only when a single property is claimed by both instruments), letting a
study run stealth for most APIs and legacy for the remainder in one browser.
That only produces a stealthy browser if legacy's detectability is confined to
the properties it wraps. It is not.

Legacy is detectable independently of which APIs it instruments, and the leaks
are catalogued in issue `#1187
<https://github.com/openwpm/OpenWPM/issues/1187>`_:

- ``Object.getPropertyDescriptor`` and ``Object.getPropertyNames`` are assigned
  onto the page-world ``Object`` in the instrument prologue, before any
  settings are consulted, and never removed
  (``Extension/src/lib/js-instruments.ts``). Neither name exists in any real
  browser, so a single ``typeof`` check identifies OpenWPM even when the
  instrumentation config is empty. Removing them is cheap and is proposed in
  PR `#1191 <https://github.com/openwpm/OpenWPM/pull/1191>`_.
- The instrument injects a ``<script>`` element carrying ``data-event-id`` and
  ``data-testing`` as the first child of ``<html>`` at ``document_start`` and
  then removes it. Randomising the event id hides the value, not the structure,
  and a page-world ``MutationObserver`` registered earlier can observe the
  insertion.
- The page-scope and content-scope halves communicate over a ``CustomEvent`` on
  ``document``. A page that patches ``dispatchEvent``/``addEventListener``
  before injection observes that traffic.

So the two instruments remain mutually exclusive, and concurrent operation is
not something to recommend until that footprint is reduced.

Reducing it is not a matter of tidying. Legacy runs in the page world by
design, because that is where in-page call stacks are reachable, and each leak
above follows from executing in the page's principal rather than from any
particular wrapper. Eliminating them means moving execution into an isolated
world — which is what the stealth instrument is. That is the reason stealth
exists as a separate instrument rather than as a hardening pass over legacy.

Legacy's detectability ceiling is architectural
-----------------------------------------------

Most of legacy's known tells are fixable with ordinary engineering discipline.
Wrapper arity (``fn.length``) and name (``fn.name``) can be copied from the
native target at no capture cost, as PR `#1210
<https://github.com/openwpm/OpenWPM/pull/1210>`_ does. Prototype pollution —
measured as 11 extra own properties on ``CanvasRenderingContext2D.prototype``,
where flattening materialises inherited members — is an implementation choice
rather than a wall: hooking each inherited member once on its owning prototype
and attributing by reading ``this`` removes it, at a data-layout and attribution
cost. Frame handling, including cross-frame access, is the same kind of problem:
more cases to cover, each of them coverable.

What does not go away is the position. A page-world wrapper can patch only its
own realm's ``Function.prototype.toString``, so the un-patched intrinsic is
always one fresh realm away —
``iframe.contentWindow.Function.prototype.toString.call(fn)`` returns the wrapper
body, measured rather than assumed. Keeping up means re-instrumenting every realm
as it is created, which is a race against the page: the instrument stays hidden
only for as long as it keeps arriving first.

Staying out of the web-content world removes the race instead of running it.
From the content script the instrument reads page objects through Xray and
exposes only what it chooses through ``exportFunction``, so it never mutates a
page intrinsic. On that surface there is no realm treadmill and no ``toString``
footprint, and frames are covered because the content script is registered for
all of them rather than because it won a race.

**The inherited frame-protection layer is the exception.** Stealth also ships a
DOM-hook layer derived from CanvasBlocker (``Extension/src/stealth/index.ts``:
``appendChild``/``document.write``/``window.open`` and iframe ``contentWindow``
access). To mask its page-facing ``Proxy`` objects it patches the main-realm
``Function.prototype.toString``, and to keep new same-origin frames instrumented
it runs exactly the treadmill described above. Both properties the
fingerprinting surface avoids are therefore present in this layer, and its
cross-realm undetectability is bounded by the ``D10-fp-*`` detection vectors
(``test/test_stealth.py``, ``test/test_pages/stealth_detection.html``) rather
than by the structural argument.

What the layer buys was measured by disabling it and re-running the suite. It is
not needed to capture inside dynamically created frames: the content script is
registered with ``allFrames`` and ``matchAboutBlank``, so the in-frame call is
still recorded and no data is lost. It is needed for attribution. ``document_url``
is taken from the sending content script's own URL, so the script auto-injected
into an ``about:blank`` frame reports ``about:blank``; the row attributing that
call to the parent page exists only because the layer's ``contentWindow`` hooks
let the parent's content script instrument the child window. With the layer
disabled, stealth's X3 output is identical to legacy's — one row, attributed to
``about:blank``.

So the footprint buys parent-context attribution for frame-local calls, and
removing it would cost that attribution rather than any captured call. The
``D10-fp-*`` rows do not measure this trade: with the hooks gone they pass
because the members are genuinely native and nothing patches
``Function.prototype.toString``, which says the surface is absent, not that it
was equivalent.

The scope of the claim is the high-value vectors the reliability paper names —
``toString``, prototype pollution, arity, name — not every conceivable tell.
Of those, only main-realm-only intrinsic patching generalises: it follows from
being a page-world wrapper at all, not from which APIs were probed.

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
- ``logFunctionsAsStrings`` **parity** and the rest of the ``logSettings``
  semantics: all nine ``logSettings`` fields are honoured **except**
  ``recursive``.
- ``recursive`` **ConfigError + sweep escape-hatch:** a recursive stealth surface
  is rejected at config-validation time with an actionable message, and
  ``openwpm/utilities/js_settings_migrator.py`` expands it into an equivalent flat
  stealth config (reporting untranslatable plain-object nodes rather than dropping
  them).
