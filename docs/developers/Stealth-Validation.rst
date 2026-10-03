How the stealth instrument is validated
=======================================

This page lists every way the stealth instrument could taint a study, and for
each risk the artefact that guards it: a test in this repository, an
experiment in PR `#1225 <https://github.com/openwpm/OpenWPM/pull/1225>`_
(stacked on this branch), or a documented, measured limit. It is meant to let a
reviewer or researcher sign off by re-running artefacts rather than by trusting
the author. Test ids are ``file::Class::test``; ``test_stealth.py`` is
``test/test_stealth.py``. All measurements are on Firefox 155.0.1.

Most browser tests compare an **uninstrumented Firefox** ("clean") with stealth
on one probe page and require the page's observations to be equal; that is
the strongest form of evidence here, because it does not depend on knowing in
advance what a page might look at.

1. A page can detect the instrument
-----------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Risk
     - Guard
     - Residual
   * - Wrapper source, arity, name, constructibility, prototype shape, leaked
       globals, ``webdriver``, stacks, settings injection
     - ``test_stealth.py::TestStealthDetectability::test_stealth_undetectable``
       (31 vectors, D1–D12, :doc:`Stealth-Requirements`), with
       ``test_legacy_detectable`` as the control
     -
   * - Anything else the page can read about the wrapped members: which page
       builtins, getters, ``toJSON`` and ``Proxy`` traps the instrument
       triggers, ``constructor`` identity, ``new`` errors, own keys, exception
       identity and stacks, cross-realm ``toString``, frame-creation members
     - ``test_stealth.py::TestStealthNativeParity::test_section_matches_uninstrumented``
       (sections ``hooks``, ``ctor``, ``construct``, ``errors``,
       ``serialization``, ``xrealm``, ``realm``, ``framehooks``: clean ==
       stealth); ``TestStealthErrorDrift`` (error identity, subclasses,
       ``DOMException``, async rejections, stacks)
     -
   * - Third-party detectors and fingerprinters
     - ``test/test_bot_detection.py::test_oss_bot_detectors_across_arms``
       (#1225): BotD, fpscanner and the paper's 35 probes; the instrument alone
       (``stealth_bare``) equals the uninstrumented baseline on all 216
       reproducible signals, and the shipped default differs from it only in
       signals that read ``navigator.webdriver`` or aggregate them.
       ``test/test_fingerprintjs_stamp.py::test_fingerprintjs_cannot_distinguish_the_arms``
       (#1225): no reproducible FingerprintJS component moves
     -
   * - The window's interface key order
     - ``TestStealthNativeParity::test_global_names_differ_only_by_early_resolved_interfaces``
     - The 18 default-surface interfaces in ``RESOLVED_BEFORE_PAGE_SCRIPT`` are
       resolved before the first page script (issue
       `#1240 <https://github.com/openwpm/OpenWPM/issues/1240>`_)
   * - Error message of a failed argument conversion
     - ``TestStealthRecordIntegrity::test_conversion_error_message``, a
       strict-xfail parity test: it expects the uninstrumented message and
       fails until the gap closes
     - ``can't convert Proxy to string`` instead of
       ``can't convert px to string``; any JavaScript wrapper does this (source
       cited in :doc:`Stealth-Instrumentation`)
   * - A scripted function sits between the page and the native
     - ``TestStealthOverflowErrors::test_no_foreign_error_reaches_the_page``
       (near the stack limit the page only ever gets page-realm errors)
     - Detectable as a scripted interposer, not as OpenWPM:
       ``arguments.callee.caller`` is ``null`` in a callback a native invokes,
       recursion depth and the argument-count limit shift ("Known residual
       tells" in :doc:`Stealth-Instrumentation`)

2. A page can hide, forge or drop records
-----------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Risk
     - Guard
     - Residual
   * - Suppressing delivery by hijacking the DOM channel
     - ``TestStealthDisruption::test_x1_stealth_channel_resists_suppression``
       (control: ``test_x1_legacy_channel_can_be_suppressed``)
     -
   * - Forging records
     - ``TestStealthDisruption::test_x2_stealth_channel_rejects_forgery``
       (control: ``test_x2_legacy_channel_can_be_forged``)
     -
   * - Hiding a call behind a deleted member and a bound copy, or inside a
       native's argument conversion
     - ``TestStealthRecordIntegrity::test_call_hidden_behind_a_deleted_member``,
       ``test_get_hidden_behind_a_deleted_accessor``,
       ``test_call_made_by_a_native_during_argument_conversion``,
       ``test_member_called_again_by_the_native``,
       ``test_call_made_while_the_instrument_reads_arguments``
     - A page can delete or redefine a wrapped property and stop it being
       recorded, as under legacy (:ref:`stealth-disruptability`)
   * - A call recorded twice, or not at all, in a reused window
     - ``TestStealthRecordIntegrity::test_reused_window_call_recorded_once``,
       ``test_dynamic_iframe_call_recorded_once``
     -
   * - Arguments the page sizes to drop a record
     - ``TestStealthRecordIntegrity::test_oversized_argument_is_truncated``,
       ``test_long_string_argument_is_truncated``,
       ``test_typed_array_argument_is_previewed`` (10 MB argument recorded in
       under 100 ms), ``test_call_with_an_uncloneable_argument``,
       ``test_primitive_after_a_truncated_argument_is_kept``
     - An argument object's own keys are listed in full, so the cost of a
       call grows with the key count of a plain-object argument

3. Records are misattributed
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Risk
     - Guard
     - Residual
   * - Wrong ``script_url`` or extension frames in ``call_stack``
     - ``TestStealthDisruption::test_attribution_stealth_records_page_script_and_clean_stack``;
       ``TestStealthRecordIntegrity::test_extension_scheme_in_page_frame_keeps_attribution``
       (a page cannot drop its frames by naming an extension scheme in its
       script URL or function name)
     - A function name containing ``@`` is prefixed to the recorded
       ``script_url``; the real URL is its suffix
   * - Wrong document or frame for calls in new frames, popups, ``blob:``,
       ``data:``, sandboxed and initial ``about:blank`` documents
     - ``TestStealthFrameOwnership::test_recorded_under_its_own_document``,
       ``TestStealthFirstLoad::test_recorded_under_its_own_document``,
       ``TestStealthDisruption::test_x3_stealth_instruments_dynamic_iframe``,
       ``TestStealthPopup::test_popup_outlives_its_opener``
     -
   * - Calls on members of a removed, navigated (also cross-site, across
       processes) or closed window, including its ``pagehide`` handler
     - ``TestStealthDeadRealm::test_recorded_under_its_own_document``,
       ``test_recorded_after_a_cross_site_navigation`` (recorded once, under
       the old document's URL, in the live tab)
     - A record whose tab has closed is kept with no tab
   * - Wrong interface for a shared-prototype method
     - ``TestStealthSharedPrototypeCapture``,
       ``TestStealthSharedPrototypeMultiMember``
     - Recorded under the owning interface; the receiver's interface is in
       the ``receiver`` column only for entries with ``receiverInterfaces``

4. The instrument changes page behaviour
----------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Risk
     - Guard
     - Residual
   * - Instrumented members return different values or errors
     - ``TestStealthNativeParity`` and ``TestStealthErrorDrift`` (above);
       ``TestStealthWindowName::test_window_name_instrumentation_undetectable``
     -
   * - Members taken from a removed, navigated or closed window stop working
     - ``TestStealthDeadRealm::test_page_observes_an_uninstrumented_firefox``
       (waits for Firefox to cut privileged wrappers, ``inner-window-nuked``)
     -
   * - Recording has side effects (e.g. reading a ``Storage`` opens its
       database)
     - ``TestStealthDeadRealm::test_page_observes_an_uninstrumented_firefox``
       (a removed frame's never-opened storage throws as in clean);
       ``TestStealthNativeParity`` section ``serialization``
     - Host objects are recorded by brand only (``[object Storage]``,
       ``[object Proxy]``)
   * - A configured constructor breaks ``new``
     - ``TestStealthConfigurability::test_constructor_members_are_left_native``
     - Constructors are refused, not instrumented
   * - ``preventSets`` blocks writes a study did not ask to block
     - ``TestStealthLogSettings::test_prevent_sets_blocks_and_logs``
     - Off in the default surface
   * - Beacons lost from ``pagehide`` during process teardown
     - ``TestStealthRecordIntegrity::test_send_beacon_not_instrumented``
       (``sendBeacon`` is not wrapped by default);
       ``test_wrapping_send_beacon_warns``
     - Any wrapped native called from ``pagehide`` while its process shuts
       down is skipped; measured with an out-of-tree probe, not automated
   * - Slower pages
     -
     - Per-window and per-call overhead, growing with the instrumented
       surface ("Performance" in :doc:`Stealth-Instrumentation`)

5. Coverage gaps
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Risk
     - Guard
     - Residual
   * - A window global the instrument never reaches (initial ``about:blank``,
       ``document.open``, frames reached through ``window[n]``, popups,
       ``blob:``/``data:``/sandboxed documents)
     - ``TestStealthFirstLoad``, ``TestStealthFrameOwnership``,
       ``TestStealthNativeParity`` section ``realm``,
       ``TestStealthDisruption::test_x3_stealth_instruments_dynamic_iframe``
     - The startup tab's ``web`` process runs no process scripts and no crawled
       page loads there (observed, not automated)
   * - Default-surface members missing
     - ``TestStealthSymbolParity::test_symbols_match_legacy``,
       ``test_key_fingerprint_symbols_present_under_stealth``,
       ``TestStealthDefaultSurface``, ``TestStealthWindowName``
     - ``navigator.sendBeacon`` is not wrapped; workers and worklets are not
       instrumented (only window globals are)
   * - A custom surface silently does not apply
     - ``TestStealthConfigurability::test_custom_settings_take_effect``,
       ``test_empty_settings_instrument_nothing``,
       ``test_entries_sharing_a_prototype_all_take_effect``,
       ``test_instance_rooted_entry_counts_depth_from_the_instance``,
       ``test_overwritten_method_is_refused``
     - An entry that instruments no member is reported in the browser console,
       not raised

6. Migrating from legacy changes what a study measures
------------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Risk
     - Guard
     - Residual
   * - Different ``symbol`` values for the same calls
     - ``TestStealthSymbolParity::test_symbols_match_legacy``
     - Shared audio methods are recorded once under the parent
       (``LEGACY_ONLY_AUDIO_SYMBOLS`` / ``STEALTH_ONLY_AUDIO_SYMBOLS``)
   * - A translated config covers less than the legacy one, silently
     - ``TestStealthRecursiveSweepParity``, ``TestStealthNarrowSweepCapture``,
       ``test_stealth.py::test_migration_golden_table``,
       ``test_stealth.py::test_migrator_reports_send_beacon``
     - Plain-object nodes, universal-prototype members, inherited accessors
       and ``sendBeacon`` are reported as untranslated (non-zero exit)
   * - Settings that behave differently
     - ``TestStealthLogSettings``, ``TestStealthLogFunctionsAsStrings``,
       ``TestStealthRecursiveRejected``,
       ``TestStealthSweepDropsPreventSets``,
       ``test_stealth.py::test_wrapping_send_beacon_warns``
     - ``recursive`` is rejected; the migrator drops ``preventSets``
   * - Different recorded values
     - ``TestStealthRecordIntegrity`` argument tests (above)
     - Legacy runs getters, ``toJSON`` and ``Proxy`` traps when recording;
       stealth records host objects by brand
       (:doc:`Stealth-and-Legacy-JS-Instruments`)

Re-running
----------

.. code-block:: bash

   pytest test/test_stealth.py -v

#1225's experiments run from its branch:
``pytest test/test_bot_detection.py test/test_fingerprintjs_stamp.py``.
