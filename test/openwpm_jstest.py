import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from openwpm.config import BrowserParams, ManagerParams
from openwpm.utilities import db_utils
from openwpm.utilities.js_settings_migrator import (
    UntranslatedEntry,
    legacy_settings_to_stealth,
)

from .js_data_backprojector import stealth_rows_to_legacy
from .openwpmtest import OpenWPMTest

#: The two instruments every :class:`OpenWPMJSTest` subclass is parametrized over.
#: ``legacy`` runs the byte-identical original test; ``stealth`` is a strictly
#: additional variant that reuses the SAME expected sets. There are deliberately
#: no mode-conditional expectations anywhere in the suite -- a class that would
#: need different expectations under stealth is not a parametrization candidate,
#: it is a stealth-native test in ``test/test_stealth.py``.
INSTRUMENT_MODES = ("legacy", "stealth")


#: Memo for :func:`transpile_cached`, keyed on the canonicalized legacy settings.
#: Process-lifetime (hence session-scoped) on purpose: every miss launches a real
#: headless Firefox (``openwpm/utilities/js_settings_migrator.py:225,475-480``),
#: so an uncached transpile would add a browser launch per parametrized test.
_TRANSPILE_CACHE: Dict[str, Tuple[List[Dict[str, Any]], List[UntranslatedEntry]]] = {}


def transpile_cached(
    legacy_settings: List[Union[str, dict]],
) -> Tuple[List[Dict[str, Any]], List[UntranslatedEntry]]:
    """Cached :func:`legacy_settings_to_stealth`.

    Returns deep copies so a caller mutating the settings (or the config
    validation pipeline rewriting them) cannot poison the cache.
    """
    key = json.dumps(legacy_settings, sort_keys=True)
    if key not in _TRANSPILE_CACHE:
        # deepcopy for the same aliasing reason as in ``get_config``: the
        # migrator runs the legacy cleaner over this list.
        _TRANSPILE_CACHE[key] = legacy_settings_to_stealth(
            copy.deepcopy(legacy_settings)
        )
    stealth_settings, untranslated = _TRANSPILE_CACHE[key]
    return copy.deepcopy(stealth_settings), list(untranslated)


class OpenWPMJSTest(OpenWPMTest):
    """Base for the JS-instrument suite, parametrized over legacy vs stealth.

    Every test method runs twice, once per :data:`INSTRUMENT_MODES` entry. The
    ``legacy`` parameter runs the original assertions unchanged; the ``stealth``
    parameter reuses those same assertions against data produced by the stealth
    instrument, with the legacy settings transpiled by
    :mod:`openwpm.utilities.js_settings_migrator`.

    Stealth is **opt-in**: :attr:`STEALTH_UNSUPPORTED_REASON` defaults to a
    non-``None`` string, so a class is skipped under ``[stealth]`` until someone
    explicitly opts it in. A ``[stealth]`` SKIP is therefore a *documented gap*,
    never a pass -- read the reason before assuming a class is covered.
    """

    #: Legacy-format ``js_instrument_settings`` for this class, or ``None`` to
    #: use the :class:`BrowserParams` default (``["collection_fingerprinting"]``).
    #: Single source of truth for BOTH modes: the stealth parameter transpiles
    #: exactly this list, so the two modes can never drift apart.
    JS_INSTRUMENT_SETTINGS: Optional[List[Union[str, dict]]] = None

    #: ``None`` means this class is opted in to the ``[stealth]`` parameter.
    #: A string means the ``[stealth]`` parameter is skipped with that reason.
    #: Reasons are specific and enumerated -- never blank, never generic.
    STEALTH_UNSUPPORTED_REASON: Optional[str] = "not yet audited for stealth"

    #: Stamped by :meth:`set_instrument_mode`; read by :meth:`get_config` and
    #: :meth:`_js_rows`.
    instrument_mode: str

    @pytest.fixture(autouse=True, params=INSTRUMENT_MODES, ids=INSTRUMENT_MODES)
    def set_instrument_mode(self, request: pytest.FixtureRequest) -> str:
        """Parametrize every test in the class over legacy/stealth."""
        if request.param == "stealth" and self.STEALTH_UNSUPPORTED_REASON:
            pytest.skip(f"stealth: {self.STEALTH_UNSUPPORTED_REASON}")
        self.instrument_mode = request.param
        return request.param

    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        manager_params.testing = True
        # Deep-copy on every read: ``clean_js_instrumentation_settings`` aliases
        # the caller's property lists into its output
        # (``openwpm/js_instrumentation.py:155``) and ``_merge_settings`` then
        # extends them in place (``:77``). Handing out the shared class
        # attribute would let one visit mutate the settings seen by the next.
        if self.instrument_mode == "legacy":
            browser_params[0].js_instrument = True
            if self.JS_INSTRUMENT_SETTINGS is not None:
                browser_params[0].js_instrument_settings = copy.deepcopy(
                    self.JS_INSTRUMENT_SETTINGS
                )
        else:
            legacy = self.JS_INSTRUMENT_SETTINGS
            if legacy is None:
                legacy = BrowserParams().js_instrument_settings
            stealth_settings, untranslated = transpile_cached(legacy)
            # ANTI-DEFANG GATE. A class that claims stealth support must
            # translate COMPLETELY. Untranslated members DISQUALIFY the class
            # (set STEALTH_UNSUPPORTED_REASON) -- they are emphatically NOT a
            # licence to subtract the missing paths from the expected set.
            assert not untranslated, (
                "class claims stealth support but the migrator could not "
                "translate: " + "; ".join(str(u) for u in untranslated)
            )
            browser_params[0].js_instrument = False
            browser_params[0].stealth_js_instrument = True
            browser_params[0].stealth_js_instrument_settings = stealth_settings
        return manager_params, browser_params

    def _js_rows(self, db: Path) -> List[Any]:
        """The single row source for every assertion in this suite.

        Under ``stealth`` the rows are back-projected into the legacy row shape;
        under ``legacy`` they are returned untouched. This is an explicit call
        rather than a monkeypatch of ``db_utils.get_javascript_entries`` on
        purpose: a global patch would be invisible at the assertion site, which
        is exactly the property a suite whose credibility rests on "the legacy
        assertion ran unmodified" cannot afford.
        """
        rows: List[Any] = db_utils.get_javascript_entries(db, all_columns=True)
        if self.instrument_mode == "stealth":
            rows = stealth_rows_to_legacy(rows)
        return rows

    def _check_calls(
        self,
        db,
        symbol_prefix,
        doc_url,
        top_url,
        expected_method_calls,
        expected_gets_and_sets,
    ):
        """Helper to check method calls and accesses in each frame"""
        # Only the row SOURCE is mode-aware; everything below this line is
        # byte-identical to the pre-parametrization version and must stay that
        # way -- that is the auditable proof no assertion was weakened.
        rows = self._js_rows(db)
        observed_gets_and_sets = set()
        observed_calls = set()
        for row in rows:
            if not row["symbol"].startswith(symbol_prefix):
                continue
            symbol = re.sub(symbol_prefix, "", row["symbol"])
            assert row["document_url"] == doc_url
            assert row["top_level_url"] == top_url
            if row["operation"] == "get" or row["operation"] == "set":
                observed_gets_and_sets.add((symbol, row["operation"], row["value"]))
            else:
                observed_calls.add((symbol, row["operation"], row["arguments"]))
        assert observed_calls == expected_method_calls
        assert observed_gets_and_sets == expected_gets_and_sets
