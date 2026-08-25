Stealth Instrumentation — Requirements & Test Matrix
====================================================

This is a lightweight requirements specification for the stealth JavaScript
instrumentation. The **detection** (D1–D4, D7, D8) and **tamper-resilience**
(X1, X2) requirements are derived directly from the reliability threats
catalogued in Krumnow, Jonker & Karsch, *"Analysing and strengthening OpenWPM's
reliability"* (`arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_,
2022, §4.1 detection, §6/RQ5–RQ8 data
integrity). Each such requirement maps to a test that asserts the **stealth**
instrument is clean; for most vectors this is paired with a **legacy** control
that demonstrates the problem, but a few (notably **D7**) are asserted only in
the stealth direction because legacy's result on them depends on the
environment or configuration (see the Confidence note below).

Requirements marked **†** (**C1, A1, D5, D6, D8b, D8c, D9, D11, D12**) are **OpenWPM
project requirements** that the paper does not name: finer-grained native-API
fidelity checks, provenance (attribution) guarantees, and runtime
configurability that the framework needs in practice but that fall outside the
paper's reliability taxonomy. **D3** and **X3** test a paper-named threat at a
finer granularity than the paper itself states (see their footnotes); they are
kept as paper-derived. Marking provenance — rather than relocating rows — keeps
the test matrix cohesive (all D* vectors live in one parametrized
``TestStealthDetectability``).

Concerns fall into two families:

- **Detectability (D)** — a page can *tell* OpenWPM's instrumentation is present
  and refuse to behave normally.
- **Disruptability (X)** — a page can *corrupt or evade* the data collection,
  silently degrading the dataset.

Tests live in ``test/test_stealth.py``; detection vectors are exercised by
``test/test_pages/stealth_detection.html``, disruption attacks by
``test/test_pages/stealth_disruption_*.html``.

Detectability requirements
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 6 22 24 14 22 18

   * - ID
     - Requirement
     - Attack mechanism (how a page detects)
     - Legacy outcome
     - Stealth defense
     - Test (result key)
   * - **D1**
     - ``navigator.webdriver`` is not exposed as ``true``
     - read ``navigator.webdriver``
     - env-dependent
     - ``overwrittenProperties: webdriver→false`` in ``settings.ts``
     - ``webdriver_flag``
   * - **D2**
     - Instrumented **functions** print the exact native source string
     - ``Function.prototype.toString.call(fn)`` on canvas / storage / WebRTC
       methods
     - wrapper body leaks ❌
     - ``exportFunction`` forwarder named after the native
     - ``canvas_functions_native``, ``storage_functions_native``, ``rtc_native``
   * - **D3** [#d3]_
     - Instrumented **getters** report ``[native code]``
     - ``toString`` of ``Navigator.prototype.userAgent`` getter
     - config-dependent — legacy wraps the ``navigator`` instance, not this
       prototype getter, so it stays native; not asserted as a control
     - native-looking getter via ``exportFunction``
     - ``navigator_native``
   * - **D4**
     - No OpenWPM globals are leaked
     - ``typeof window.getInstrumentJS / jsInstruments /
       instrumentFingerprintingApis``
     - legacy injects ``window.getInstrumentJS`` ❌
     - nothing added to page global scope
     - ``no_global_leaks``
   * - **D5** †
     - ``constructor`` on instrumented objects is the interface object
     - ``obj.constructor === Iface``, ``Object.getPrototypeOf(obj).constructor
       === Iface``
     - reading ``constructor`` throws ``too much recursion`` ❌ (control asserted)
     - ``constructor`` is never replaced
     - ``constructors_present``
   * - **D6** †
     - ``Function.prototype.bind`` integrity
     - compare ``bind.toString()`` shape
     - tamper check
     - ``bind`` untouched
     - ``bind_integrity``
   * - **D7**
     - Error stacks free of ``moz-extension://``
     - force an error, inspect ``e.stack``
     - depends on injection path
     - exceptions are not caught; the engine hides extension frames from the
       page
     - ``clean_error_stacks``
   * - **D8**
     - No prototype pollution / no extra props
     - ``Object.getOwnPropertyNames(Object.prototype)`` members must NOT be
       **own** properties of an instrumented prototype (e.g.
       ``CanvasRenderingContext2D.prototype``)
     - legacy flattens ancestor prototypes ❌ — ``Object.getPropertyNames``
       concatenates the whole chain and each name is ``defineProperty``'d back
       onto the first object, so ``hasOwnProperty``/``valueOf``/``isPrototypeOf``/…
       leak down as own properties
     - per-prototype overwrite leaves the chain shape intact
     - ``no_extra_prototype_properties``
   * - **D8b** †
     - Instrumented **functions** report the native **arity** (``.length``)
     - compare ``canvas.getContext.length`` (native ``1``) against the wrapper
     - legacy wrapper is ``function () {…}`` → ``.length === 0`` ❌
     - ``makeArityForwarder`` codegens a forwarder with the native param count
     - ``function_arity_native``
   * - **D8c** †
     - Instrumented **accessors** report the native function **name**
       (``get userAgent``)
     - read ``Object.getOwnPropertyDescriptor(...).get.name``
     - env/config-dependent
     - the wrapped accessor restores the spec-prefixed ``get <name>``
     - ``accessor_name_native``
   * - **D9** †
     - No instrument helpers leak onto the page's ``Object``
     - probe the page's own ``Object``/``Object.prototype`` for the walk helpers
     - env/config-dependent (legacy defines none either)
     - helpers live only in the instrument's sandbox compartment
     - ``no_instrument_helpers_leaked``
   * - **D11** †
     - ``Function.prototype.toString`` is the untouched native
     - stringify ``Function.prototype.toString`` with itself
     - not touched by legacy either
     - ``toString`` is never patched
     - ``tostring_recursive_native``
   * - **D12** †
     - A custom surface does not become a detection hook
     - look for the name an injected settings global would use on the page's
       window
     - n/a — legacy injects its configuration differently
     - settings reach the instrument through ``sharedData`` and its sandbox,
       never the page; checked with a custom surface configured
     - ``no_stealth_settings_leak``

All D* vectors are proven by a single parametrized test that asserts the stealth
instrument is clean for every vector, paired with a control that asserts legacy
trips the empirically-confirmed vectors. ``TestStealthDetectability`` proves both
directions:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDetectability.test_stealth_undetectable

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDetectability.test_legacy_detectable

D7 additionally has a dedicated, stronger proof:
``TestStealthErrorDrift.test_instrumented_throw_stack_has_no_extension_frames``
throws *through* an instrumented native method and asserts the page's view of
the error's stack carries no ``moz-extension://`` frame, and
``test_every_observation_matches_uninstrumented`` requires the error's
identity, own properties, ``lineNumber`` and full ``stack`` to match an
uninstrumented run.

Beyond these single-vector rows, ``TestStealthNativeParity`` runs
``stealth_native_parity.html`` in an uninstrumented Firefox and under stealth
and requires every observation to be identical: which page builtins the
instrument calls or which page getters, ``toJSON`` methods and ``Proxy`` traps
it triggers (none), ``constructor`` identity, constructibility and the
``TypeError`` on ``new``, own keys, exact ``toString``/``.length``/``.name``,
exception identity and shape, and the exact ``toString`` of each hook as seen
from three kinds of same-origin iframe realm.

.. note::

   **Confidence note.** The ``legacy_detectable`` flags reflect recorded
   legacy detection-page results, and every run of
   ``TestStealthDetectability`` re-asserts the controls (Firefox 155.0.1):

   - **Legacy provably DETECTED (control asserted):** D1 ``webdriver_flag``
     (Selenium sets ``navigator.webdriver=true``; legacy never overrides it),
     D2 ``canvas/storage/rtc`` (wrapper bodies leak via ``toString``),
     D4 ``no_global_leaks`` (legacy injects ``window.getInstrumentJS``),
     D5 ``constructors_present`` (legacy's chain manipulation triggers
     ``too much recursion`` when reading ``constructor``), D8
     ``no_extra_prototype_properties`` (ancestor-prototype flattening — see the
     D8 row above), and D8b ``function_arity_native`` (the legacy wrapper has
     ``.length === 0`` where the native function declares a non-zero arity).
   - **Legacy not reliably detected (stealth-only, ``None``):** D3
     ``navigator_native`` (the legacy fingerprinting collection instruments the
     ``window.navigator`` *instance*, not the ``Navigator.prototype.userAgent``
     getter the page probes, so that getter stays native), D6 ``bind_integrity``,
     D7 ``clean_error_stacks``, D8c ``accessor_name_native`` (which accessors
     legacy wraps is config-dependent), and D9 ``no_instrument_helpers_leaked``
     (legacy defines no such helpers either).

   The **stealth** direction is asserted unconditionally for every parametrized
   vector: the 13 D1–D9 vectors, the 16 D10 rows, D11 and D12.

Frame-creation detection vectors (D10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The vectors above probe the **fingerprinting** instrument. A page-scope layer
that learned of new frames by replacing ``Node.prototype.appendChild``,
``document.write``, ``window.open`` or the
``HTMLIFrameElement.prototype.contentWindow`` getter would leave its own
``toString`` / arity / name / cross-realm tells. Stealth learns of new frames
from its window actor instead and replaces none of these members; the D10 rows
in ``test/test_pages/stealth_detection.html`` lock that in. All 16 are
**stealth-only** (``legacy_detectable=None``): legacy does not hook these
members either.

.. list-table::
   :header-rows: 1
   :widths: 40 38 22

   * - ID
     - Requirement
     - Test result key
   * - **D10-fp-appendChild-native**
     - ``Node.prototype.appendChild`` same-realm ``toString`` is
       ``[native code]``
     - ``fp_appendChild_native``
   * - **D10-fp-appendChild-arity**
     - ``appendChild.length`` matches native arity
     - ``fp_appendChild_arity``
   * - **D10-fp-appendChild-name**
     - ``appendChild.name`` matches native name
     - ``fp_appendChild_name``
   * - **D10-fp-appendChild-xrealm**
     - fresh-realm ``toString`` on ``appendChild`` is ``[native code]``
     - ``fp_appendChild_xrealm_native``
   * - **D10-fp-docwrite-native**
     - ``document.write`` same-realm ``toString`` is native
     - ``fp_docwrite_native``
   * - **D10-fp-docwrite-arity**
     - ``document.write.length`` matches native
     - ``fp_docwrite_arity``
   * - **D10-fp-docwrite-name**
     - ``document.write.name`` matches native
     - ``fp_docwrite_name``
   * - **D10-fp-docwrite-xrealm**
     - fresh-realm ``toString`` on ``document.write`` is native
     - ``fp_docwrite_xrealm_native``
   * - **D10-fp-window-open-native**
     - ``window.open`` same-realm ``toString`` is native
     - ``fp_window_open_native``
   * - **D10-fp-window-open-arity**
     - ``window.open.length`` matches native
     - ``fp_window_open_arity``
   * - **D10-fp-window-open-name**
     - ``window.open.name`` matches native
     - ``fp_window_open_name``
   * - **D10-fp-window-open-xrealm**
     - fresh-realm ``toString`` on ``window.open`` is native
     - ``fp_window_open_xrealm_native``
   * - **D10-fp-contentwindow-getter-native**
     - ``contentWindow`` getter same-realm ``toString`` is native
     - ``fp_contentwindow_getter_native``
   * - **D10-fp-contentwindow-getter-arity**
     - ``contentWindow`` getter ``.length`` matches native
     - ``fp_contentwindow_getter_arity``
   * - **D10-fp-contentwindow-getter-name**
     - ``contentWindow`` getter ``.name`` is native (``get contentWindow``)
     - ``fp_contentwindow_getter_name``
   * - **D10-fp-contentwindow-getter-xrealm**
     - fresh-realm ``toString`` on ``contentWindow`` getter is native
     - ``fp_contentwindow_xrealm_native``

.. note::

   The ``*-xrealm`` rows check the exact string from two other realms; ``TestStealthNativeParity`` additionally compares it, in both
   directions, for an appended ``about:blank`` iframe, one inserted with
   ``Element.after`` and reached through ``window[n]``, and a loaded
   same-origin iframe.

Disruptability requirements
---------------------------

These are the paper's data-integrity attacks (RQ5–RQ8). The legacy instrument
ships records page→extension via ``document.dispatchEvent(new CustomEvent(eventId,
…))`` (``content/javascript-instrument-page-scope.ts``), relayed by a
``document.addEventListener(eventId, …)`` listener
(``content/javascript-instrument-content-scope.ts``). Both the dispatcher and
the event id are reachable from page script, so a hostile page can suppress or
forge records. The stealth instrument sends records from its sandbox over the
process message manager (``stealth/actor.ts``,
``privileged/stealthInstrument/``), which page script cannot reach.

.. list-table::
   :header-rows: 1
   :widths: 6 22 26 16 16 14

   * - ID
     - Requirement
     - Attack mechanism
     - Legacy outcome
     - Stealth defense
     - Test
   * - **X1**
     - A page cannot **suppress** record delivery
     - override ``document.dispatchEvent`` to swallow events, then call
       instrumented APIs
     - post-hijack calls dropped ❌
     - privileged messaging bypasses the DOM
     - ``stealth_disruption_suppress.html``
   * - **X2**
     - A page cannot **forge** records
     - grab ``eventId`` (via an intercepted dispatch), emit
       ``CustomEvent(eventId, {detail:[forged]})``
     - forged rows enter the DB ❌
     - no page-reachable channel to inject into
     - ``stealth_disruption_forge.html``
   * - **X3** [#x3]_
     - Dynamically-created **iframes** are instrumented
     - JS-create a navigating iframe and run an API call in its initial
       ``about:blank`` document, where no content script runs
     - call not recorded ❌
     - the window actor instruments every window global when it is
       created
     - ``stealth_disruption_iframe.html``

X1 (suppression) is proven by a control that shows legacy loses records and an
assertion that stealth keeps them:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x1_legacy_channel_can_be_suppressed

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x1_stealth_channel_resists_suppression

X2 (forgery) is proven by a control that shows legacy accepts a forged row and
an assertion that stealth rejects it:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x2_legacy_channel_can_be_forged

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x2_stealth_channel_rejects_forgery

X3 (dynamic iframes) is proven by asserting stealth records the in-iframe call
once, under the frame's ``about:blank`` document and its ``frame_id``, while
legacy does not record it (see the attribution note below):

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x3_stealth_instruments_dynamic_iframe

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x3_legacy_misses_dynamic_iframe_call

.. note::

   **Frame attribution.** A call is recorded under the ``document_url`` and
   ``frame_id`` of the document it runs in, whichever DOM method inserted the
   frame: the initial ``about:blank`` document of a frame or popup that is
   navigating (legacy does not record these calls), the document that then
   loads, and ``blob:``, ``data:`` and sandboxed documents (legacy does not
   record these). ``document_url`` is the document's URL when the call is
   made, so a document that ``document.open`` gave its opener's URL is
   recorded under that URL. A member called after its window is removed,
   navigated away or closed is recorded under that window's last URL, not
   the frame's current document.

   Each call is recorded exactly once; the tests assert exact row counts.

Attribution requirement
------------------------

**† OpenWPM project requirement** — not a reliability concern named in
`arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_. The clean-stack half
overlaps the paper's stack-trace
detection vector (D7), but treating call attribution / provenance correctness as
a requirement is an OpenWPM data-quality need, not a threat the paper catalogues.

.. list-table::
   :header-rows: 1
   :widths: 6 22 24 34 14

   * - ID
     - Requirement
     - Why it matters
     - Stealth defense
     - Test
   * - **A1** †
     - Records attribute to the **page script** with a stack free of extension
       frames
     - a polluted ``call_stack`` (or wrong ``script_url``) corrupts provenance
       analysis and re-leaks ``moz-extension://``
     - ``instrument.ts`` parses ``script_url`` from the first non-extension frame;
       the recorded ``call_stack`` then has **every** extension frame filtered out
       (matching the literal ``moz-extension://`` scheme, not just this
       extension's UUID), so an API invoked purely from instrumentation, or a page
       that calls back into instrumented APIs, can never leak ``moz-extension://``
       — even a co-installed extension's frame. When no page frame remains the
       context is blank. Stack collection is gated by the per-object
       ``logSettings.logCallStack`` flag (honoured like legacy), so the
       attribution test runs with a custom surface that sets ``logCallStack: true``
       for the canvas object, which doubly proves the flag is respected.
     - ``stealth_attribution.html``

A1 is proven by asserting the stealth record names the page script with a clean
stack, paired with a legacy reference:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_attribution_stealth_records_page_script_and_clean_stack

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_attribution_legacy_records_page_script

Configurability requirement
----------------------------

**† OpenWPM project requirement** — not a reliability concern named in
`arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_. The paper does not
treat selective or configurable
instrumentation as a stated requirement or design goal; this is purely an
operational need (run studies without forking the extension).

.. list-table::
   :header-rows: 1
   :widths: 6 22 24 34 14

   * - ID
     - Requirement
     - Why it matters
     - Mechanism
     - Test
   * - **C1** †
     - The instrumented surface is **runtime-configurable**
     - studies must instrument arbitrary APIs without forking the extension
     - ``browser_params.stealth_js_instrument_settings`` (defaults to ``None`` →
       bundled ``settings.ts``) is validated against
       ``schemas/js_instrument_settings.schema.json`` and handed to content
       processes through ``sharedData``
     - ``TestStealthConfigurability``

C1 is proven by asserting a custom surface actually replaces the default and
still passes every detection vector:

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthConfigurability.test_custom_settings_take_effect

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthConfigurability.test_custom_settings_stay_undetectable

.. note::

   A custom surface uses bare global names for
   ``object`` (e.g. ``"CanvasRenderingContext2D"``, ``"Navigator"``,
   ``"document"``), the full stealth shape (top-level ``depth``, nested
   ``propertiesToInstrument`` ``{depth, propertyNames}``, and
   ``overwrittenProperties``). When unset, the bundled default is used, so
   existing behaviour is unchanged.

Test matrix summary
-------------------

Each requirement is a separate, named test so failures are traceable to a
specific concern. To keep browser launches bounded, the detection page is run
**once per mode** (class-scoped fixtures) and every D* test asserts against the
shared results; X* tests each run their own attack page per mode.

- **D1–D12** → ``TestStealthDetectability`` — ``test_stealth_undetectable[D*]``
  (asserts stealth clean, all 31 parametrized vectors) and
  ``test_legacy_detectable`` (asserts legacy trips the empirically-confirmed
  vectors: D1, D2×3, D4, D5, D8, D8b).
- **X1** → ``TestStealthDisruption`` — ``test_x1_legacy_channel_can_be_suppressed``
  (control: legacy loses records) and
  ``test_x1_stealth_channel_resists_suppression`` (stealth keeps them).
- **X2** → ``TestStealthDisruption`` — ``test_x2_legacy_channel_can_be_forged``
  (control: legacy accepts the forged ``FORGED.injectedByPage`` row) and
  ``test_x2_stealth_channel_rejects_forgery`` (stealth rejects it).
- **A1** → ``TestStealthDisruption`` —
  ``test_attribution_stealth_records_page_script_and_clean_stack`` (stealth
  ``script_url`` names the page and ``call_stack`` has no ``moz-extension://``)
  with ``test_attribution_legacy_records_page_script`` as reference.
- **C1** → ``TestStealthConfigurability`` — ``test_custom_settings_take_effect``
  (a custom ``instrumentedName`` proves the configured surface replaced the
  default) and ``test_custom_settings_stay_undetectable`` (a custom surface still
  passes every D* vector).
- **X3** → ``TestStealthDisruption`` —
  ``test_x3_stealth_instruments_dynamic_iframe`` (stealth records the
  dynamic-iframe ``toDataURL`` once, under ``about:blank`` and the frame's
  ``frame_id``) and
  ``test_x3_legacy_misses_dynamic_iframe_call`` (legacy does not record it).
  See the frame attribution note above.

.. note::

   The browser-driven tests require a Firefox + xpi run to validate. They are
   part of ``test/test_stealth.py``, which CI runs on every pull request and
   merge (``scripts/ci.sh`` discovers the suite via ``pytest-split`` across its
   test groups).

.. rubric:: Provenance footnotes

.. [#d3] **Paper-named threat, project-refined granularity.** §4.1 names the
   ``toString`` ``[native code]`` vector for **functions** (D2) but does not
   separately call out the **getter** ``toString``. D3 tests the same vector at a
   finer grain; the threat is the paper's, the getter-specific check is the
   project's.

.. [#x3] **Paper-named threat, project-refined granularity.** §6/RQ8 names
   *unobserved channels* including iframe-injection bugs where an iframe escapes
   instrumentation. The paper's threat is "iframe escapes instrumentation"; the
   specific case tested here — a call into the initial ``about:blank``
   document of a navigating frame, which no content script runs in — is the
   project's empirical refinement (see the frame attribution note above).
