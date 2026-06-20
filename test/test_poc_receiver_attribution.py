"""PROOF-OF-CONCEPT: clean prototype instrumentation AND per-instance receiver
attribution simultaneously (ADR-0001 gap #2 — "lose the receiver").

This test drives a REAL Firefox + the stealth WebExtension. It instruments
``EventTarget.prototype.addEventListener`` ONCE on the shared prototype (a clean,
in-place prototype redefine — no own-property, native toString/arity) and calls
it on two distinct ``XMLHttpRequest`` instances (one of them twice). The PoC
WeakMap in ``Extension/src/stealth/instrument.ts`` assigns a per-instance id,
keyed on the Xray-wrapped page object held in the isolated content-script world.

It asserts BOTH:
  (a) per-instance attribution — two distinct instances -> two distinct ids,
      the same instance called twice -> the SAME id (THE CRUX: stable Xray
      WeakMap keying), and
  (b) the instrument stayed clean + undetectable (self-reported vectors).

Reuses the proven harness helpers from ``test_stealth`` (``_run_page``,
``_collect_results``, ``_stealth_params``).
"""

from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from openwpm.config import BrowserParams, ManagerParams
from openwpm.utilities import db_utils

from .test_stealth import _collect_results, _run_page, _stealth_params
from .utilities import ServerUrls

POC_PAGE = "/stealth_poc_receiver.html"

# Hook addEventListener ONCE on the shared EventTarget.prototype, attributing only
# calls whose receiver interface is XMLHttpRequest. This is the exact clean
# shared-prototype path; the PoC adds a per-instance id to the `receiver` value.
POC_STEALTH_SETTINGS: List[Dict] = [
    {
        "object": "EventTarget",
        "instrumentedName": "EventTarget",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["addEventListener"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
            "receiverInterfaces": ["XMLHttpRequest"],
        },
    },
]


def _poc_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = POC_STEALTH_SETTINGS
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestPocReceiverAttribution:
    def test_per_instance_attribution_is_stable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Two distinct instances -> two ids; one instance twice -> one id.

        THE CRUX: a WeakMap keyed on the Xray-wrapped page object must give a
        STABLE key across calls. If Xray re-created wrappers per crossing, the
        same instance would map to two ids (ADR vindicated). We assert it does
        not.
        """
        data_dir = tmp_path_factory.mktemp("poc_attr")
        db_path = _run_page(_poc_params(data_dir), server.base + POC_PAGE)

        rows = db_utils.query_db(
            db_path,
            "SELECT receiver FROM javascript "
            "WHERE symbol = ? AND receiver IS NOT NULL "
            "ORDER BY event_ordinal",
            ("EventTarget.addEventListener",),
        )
        receivers = [r[0] for r in rows]

        # Page made exactly 3 instrumented addEventListener calls on XHR:
        #   xhrA twice, xhrB once. (Non-XHR receivers are filtered content-side.)
        assert len(receivers) == 3, (
            f"expected 3 attributed XHR addEventListener calls, got "
            f"{len(receivers)}: {receivers}"
        )

        # Every receiver must be interface-attributed AND per-instance tagged.
        for rcv in receivers:
            assert rcv is not None and rcv.startswith("XMLHttpRequest#"), (
                f"receiver not per-instance attributed: {rcv!r}"
            )

        distinct = set(receivers)
        # CRUX (a): exactly two distinct instances were touched.
        assert len(distinct) == 2, (
            f"expected exactly 2 distinct per-instance receiver ids "
            f"(xhrA, xhrB), got {len(distinct)}: {sorted(distinct)} from "
            f"{receivers}"
        )

        # CRUX (b): the instance called twice yields the SAME id twice — i.e. the
        # Xray WeakMap key is stable across calls.
        from collections import Counter

        counts = Counter(receivers)
        most_common_id, most_common_n = counts.most_common(1)[0]
        assert most_common_n == 2, (
            f"the instance called twice did NOT collapse to one stable id; "
            f"counts={dict(counts)} — Xray WeakMap keying is UNSTABLE "
            f"(ADR vindicated)"
        )

    def test_stayed_clean_and_undetectable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """The per-instance attribution added no detection surface."""
        data_dir = tmp_path_factory.mktemp("poc_detect")
        results = _collect_results(_poc_params(data_dir), server.base + POC_PAGE)
        assert results, "no PoC self-report collected"
        expected_true = [
            "addeventlistener_native",
            "no_own_property_pollution",
            "no_global_leaks",
            "no_instrument_helpers_leaked",
            "constructor_read_through_xray",
        ]
        for key in expected_true:
            assert results.get(key) is True, (
                f"detection vector '{key}' did not pass "
                f"(value={results.get(key)!r}, "
                f"error={results.get(key + '_error')!r})"
            )
