Stealth JavaScript Instrument
=============================

The **stealth** JavaScript instrument is an alternative to the legacy
``js_instrument`` for recording how a page uses Web APIs (canvas, navigator,
storage, ...). It captures the same kind of per-call data, delivers it over a
channel the page cannot reach, and is built so that a page observes the same
values it would in an uninstrumented Firefox. Internals:
:doc:`developers/Stealth-Instrumentation`.

Why use the stealth instrument
------------------------------

It addresses the reliability problems found in [Krumnow2022]_:

- **Much harder to detect.** A page that notices it is being measured can
  change its behaviour or refuse to run, skewing your dataset. The stealth
  instrument is tested differentially: a probe page must observe identical
  values with and without it (:doc:`developers/Stealth-Validation`). The tells
  that remain, and what is not recorded (workers), are listed under
  :ref:`stealth-residual-tells`.
- **Tamper-resistant data delivery.** The legacy instrument's records travel
  over a channel a hostile page can reach to drop them or forge fake ones; the
  stealth instrument's do not. A page can still stop a property from being
  recorded by deleting or redefining it, as under legacy
  (:ref:`stealth-disruptability`).

In exchange it records some things differently (:ref:`stealth-what-changes`);
:doc:`developers/Stealth-and-Legacy-JS-Instruments` explains when legacy is
still the right choice. If you do not need stealthiness, the legacy
``js_instrument`` remains available.

Enabling the stealth instrument
-------------------------------

.. code-block:: python

   browser_params.stealth_js_instrument = True
   browser_params.js_instrument = False  # leave the legacy instrument off

The two instruments are mutually exclusive: enabling both raises a
``ConfigError`` when the configuration is validated.

Customising what gets instrumented
----------------------------------

The flag alone instruments a built-in set of fingerprinting-relevant APIs; how
it compares with legacy's ``collection_fingerprinting`` is under
:ref:`stealth-what-changes`. To choose the APIs and properties yourself, set
``stealth_js_instrument_settings`` on ``BrowserParams``:

.. code-block:: python

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
           },
       },
       # ... more entries ...
   ]

Left unset (``None``), the bundled default surface is used; an empty list
instruments nothing. Several entries may resolve to the same prototype; each
member is instrumented once, under the first entry that lists it.

The default leaves ``navigator.sendBeacon`` unwrapped; why, and how to record
beacons with ``http_instrument`` instead: :ref:`stealth-send-beacon`.

The shape of a settings entry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``object`` (required): the **bare global name** to instrument, looked up in
  the page's global scope. Usually an *interface*, MDN's term for the named
  type whose prototype the page's objects share: ``"CanvasRenderingContext2D"``,
  ``"Navigator"``, ``"Storage"``. It can also be a global object, which is why
  ``"document"`` and ``"window"`` are lowercase: they name single existing
  objects, not types. A legacy ``window['...']`` path is rejected
  (:ref:`stealth-object-naming`).
- ``instrumentedName`` (required): the name this object is recorded under. It is
  not inferred from ``object``; the schema rejects an entry without it.
- ``depth`` (optional, default 0): a prototype-chain offset from ``object``;
  with an empty ``propertiesToInstrument``, every prototype up to it is
  instrumented.
- ``logSettings`` (required): which methods and properties to capture and which
  kinds of access (calls, reads, writes) to log (:ref:`stealth-log-settings`).

Any other field is rejected. One ``ConfigError`` lists every problem in the
settings, each with where it is.

Known limitations
-----------------

The stealth instrument hooks each Web API at the **prototype level rather than
on individual objects**, so every canvas context, navigator access and storage
object is covered without knowing in advance which objects a page creates.

When several interfaces inherit a member from a shared ancestor, the hook sits
on the ancestor that owns it, so ``symbol`` names the ancestor
(``AudioNode.connect``), not the interface the page reached it through. The
``receiver`` column records the interface of the object each call, get or set
was made on (``GainNode``), and ``openwpm.utilities.db_utils.legacy_symbol``
turns the two into the ``symbol`` legacy would have recorded
(:ref:`stealth-what-changes`). What is lost is never the call, only the path by
which the page arrived at the member.

.. [Krumnow2022] Krumnow, Jonker & Karsch, *"Analysing and strengthening
   OpenWPM's reliability"*, `arXiv:2205.08890
   <https://arxiv.org/abs/2205.08890>`_, 2022.
