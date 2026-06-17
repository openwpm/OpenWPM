Stealth Instrumentation — Requirements & Test Matrix
====================================================

Requirements for the stealth instrument, each a separately named test in
``test/test_stealth.py``. Detection vectors are exercised by
``test/test_pages/stealth_detection.html``, disruption attacks by
``test/test_pages/stealth_disruption_*.html``.

- **Detectability (D)** — a page can *tell* the instrumentation is present and
  refuse to behave normally.
- **Disruptability (X)** — a page can *corrupt or evade* the data collection.

D1–D4, D7, D8, X1 and X2 are the reliability threats catalogued in Krumnow,
Jonker & Karsch, *"Analysing and strengthening OpenWPM's reliability"*
(`arXiv:2205.08890 <https://arxiv.org/abs/2205.08890>`_, 2022; §4.1 detection,
§6/RQ5–RQ8 data integrity); D3 and X3 test a paper-named threat at a finer
granularity (footnotes). Rows marked **†** (**C1, A1, D5, D6, D8b, D8c, D9, D11**) are
OpenWPM project requirements the paper does not name: native-API fidelity,
provenance and runtime configurability.

The detection page runs once per mode (class-scoped fixtures) and every D test
asserts against the shared results; each X test runs its own attack page per
mode. The browser tests need Firefox and the built xpi; CI runs them on every
pull request and merge (``scripts/ci.sh``, split across test groups by
``pytest-split``).

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
     - reads ``true``: Firefox sets it under WebDriver and legacy never
       overrides it ❌
     - ``overwrittenProperties`` sets ``webdriver`` to ``false`` in ``settings.ts``
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
     - config-dependent: the legacy preset wraps the ``window.navigator``
       instance, not this getter, which stays native
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
     - legacy's chain manipulation makes reading ``constructor`` throw
       ``too much recursion`` ❌
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
     - flattens ancestor prototypes ❌: ``Object.getPropertyNames``
       concatenates the whole chain and each name is ``defineProperty``'d onto
       the first object, so ``hasOwnProperty``/``valueOf``/``isPrototypeOf``/…
       become own properties
     - per-prototype overwrite leaves the chain shape intact
     - ``no_extra_prototype_properties``
   * - **D8b** †
     - Instrumented **functions** report the native **arity** (``.length``)
     - compare ``canvas.getContext.length`` (native ``1``) against the wrapper
     - wrapper is ``function () {…}``, so ``.length === 0`` ❌
     - ``makeArityForwarder`` codegens a forwarder with the native param count
     - ``function_arity_native``
   * - **D8c** †
     - Instrumented **accessors** report the native function **name**
       (``get userAgent``)
     - read ``Object.getOwnPropertyDescriptor(...).get.name``
     - env/config-dependent (which accessors legacy wraps)
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

``TestStealthDetectability`` asserts stealth is clean on every parametrized
vector (the 13 D1–D9 vectors, the 16 D10 rows and D11) and, as a control, that
legacy trips D1, D2×3, D4, D5, D8 and D8b (❌ above; recorded legacy results,
re-asserted every run). The other vectors are stealth-only
(``legacy_detectable=None``): legacy's result depends on the environment or
configuration, or legacy does not touch the probed member.

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDetectability.test_stealth_undetectable

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDetectability.test_legacy_detectable

D7 also has a direct proof:
``TestStealthErrorDrift.test_instrumented_throw_stack_has_no_extension_frames``
throws *through* an instrumented native and asserts the page's view of the
stack has no ``moz-extension://`` frame, and
``test_every_observation_matches_uninstrumented`` requires the error's
identity, own properties, ``lineNumber`` and full ``stack`` to match an
uninstrumented run.

``TestStealthNativeParity`` complements the single-vector rows: every
observation ``stealth_native_parity.html`` makes must be identical in an
uninstrumented Firefox and under stealth (what it covers:
:doc:`Stealth-Validation`, section 1).

Frame-creation detection vectors (D10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A page-scope layer that learned of new frames by replacing the members below
would leave its own ``toString``, arity, name and cross-realm tells. Stealth
learns of new frames from its window actor and replaces none of them. All 16
rows are stealth-only (``legacy_detectable=None``): legacy does not hook these
members either. IDs are ``D10-fp-<member>-<check>``; cells are result keys.

.. list-table::
   :header-rows: 1
   :widths: 24 19 19 19 19

   * - Member (``<member>``)
     - ``native``: same-realm ``toString`` is ``[native code]``
     - ``arity``: ``.length`` matches native
     - ``name``: ``.name`` matches native
     - ``xrealm``: fresh-realm ``toString`` is ``[native code]``
   * - ``Node.prototype.appendChild`` (``appendChild``)
     - ``fp_appendChild_native``
     - ``fp_appendChild_arity``
     - ``fp_appendChild_name``
     - ``fp_appendChild_xrealm_native``
   * - ``document.write`` (``docwrite``)
     - ``fp_docwrite_native``
     - ``fp_docwrite_arity``
     - ``fp_docwrite_name``
     - ``fp_docwrite_xrealm_native``
   * - ``window.open`` (``window-open``)
     - ``fp_window_open_native``
     - ``fp_window_open_arity``
     - ``fp_window_open_name``
     - ``fp_window_open_xrealm_native``
   * - ``HTMLIFrameElement.prototype.contentWindow`` getter
       (``contentwindow-getter``)
     - ``fp_contentwindow_getter_native``
     - ``fp_contentwindow_getter_arity``
     - ``fp_contentwindow_getter_name`` (``get contentWindow``)
     - ``fp_contentwindow_xrealm_native``

The ``xrealm`` checks compare the exact string from two other realms;
``TestStealthNativeParity`` also compares it, in both directions, for an
appended ``about:blank`` iframe, one inserted with ``Element.after`` and reached
through ``window[n]``, and a loaded same-origin iframe.

Disruptability requirements
---------------------------

The paper's data-integrity attacks (RQ5–RQ8). Legacy ships records via
``document.dispatchEvent(new CustomEvent(eventId, …))``
(``content/javascript-instrument-page-scope.ts``), relayed by a
``document.addEventListener(eventId, …)`` listener
(``content/javascript-instrument-content-scope.ts``); page script can reach
both the dispatcher and the event id. Stealth sends records from its sandbox
over the process message manager (``stealth/actor.ts``,
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

X1: legacy loses records after the hijack; stealth keeps them.

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x1_legacy_channel_can_be_suppressed

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x1_stealth_channel_resists_suppression

X2: legacy accepts the forged ``FORGED.injectedByPage`` row; stealth rejects
it.

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x2_legacy_channel_can_be_forged

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x2_stealth_channel_rejects_forgery

X3: stealth records the in-iframe ``toDataURL`` once, under the frame's
``about:blank`` document and its ``frame_id``; legacy does not record it.

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x3_stealth_instruments_dynamic_iframe

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_x3_legacy_misses_dynamic_iframe_call

.. _stealth-frame-attribution:

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
-----------------------

**†** Provenance correctness is an OpenWPM data-quality need, not a threat the
paper catalogues; its clean-stack half overlaps D7.

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
     - ``instrument.ts`` takes ``script_url`` from the first non-extension
       frame and filters **every** extension frame out of ``call_stack`` by the
       literal ``moz-extension://`` scheme, not this extension's UUID, so
       neither an API invoked purely from instrumentation, a page calling back
       into instrumented APIs, nor a co-installed extension's frame leaks it.
       With no page frame left the context is blank. Stack collection is gated
       by the per-object ``logSettings.logCallStack`` (as legacy), so the test
       uses a custom surface with ``logCallStack: true`` for the canvas object,
       which also proves the flag is honoured.
     - ``stealth_attribution.html``

A1: the stealth record names the page script with a clean stack; legacy as
reference.

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_attribution_stealth_records_page_script_and_clean_stack

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthDisruption.test_attribution_legacy_records_page_script

Configurability requirement
---------------------------

**†** An operational need the paper does not treat: running studies without
forking the extension.

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
     - ``browser_params.stealth_js_instrument_settings`` (``None`` means the bundled
       ``settings.ts``), validated against
       ``schemas/stealth_js_instrument_settings.schema.json`` and handed to
       content processes through ``sharedData``; format in
       :ref:`stealth-configuring`
     - ``TestStealthConfigurability``

C1: a custom surface, identified by a distinctive ``instrumentedName``,
replaces the default and still passes every D vector.

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthConfigurability.test_custom_settings_take_effect

.. literalinclude:: ../../test/test_stealth.py
   :language: python
   :pyobject: TestStealthConfigurability.test_custom_settings_stay_undetectable

.. rubric:: Provenance footnotes

.. [#d3] §4.1 names the ``toString`` ``[native code]`` vector for **functions**
   (D2), not separately for **getters**; D3 applies the paper's threat at that
   finer grain.

.. [#x3] §6/RQ8 names *unobserved channels*, including iframe-injection bugs
   where an iframe escapes instrumentation. The case tested here, a call in
   the initial ``about:blank`` document of a navigating frame, which no
   content script runs in, is the project's empirical refinement (see the
   frame attribution note above).
