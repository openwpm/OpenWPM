import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openwpm.config import BrowserParams, ManagerParams
from openwpm.utilities import db_utils

from .openwpmtest import OpenWPMTest


class OpenWPMJSTest(OpenWPMTest):
    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].js_instrument = True
        manager_params.testing = True
        return manager_params, browser_params

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
        rows = db_utils.get_javascript_entries(db, all_columns=True)
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

    def _assert_exfil_json(
        self, db: Path, symbol: str, expected: Dict[str, Any]
    ) -> None:
        """Merge the JSON objects the page wrote to the instrumented string
        property ``symbol`` and compare them to ``expected``."""
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        merged: Dict[str, Any] = {}
        for row in rows:
            assert isinstance(row, sqlite3.Row)
            if row["symbol"] != symbol or row["operation"] != "set":
                continue
            merged.update(json.loads(row["value"]))
        assert merged == expected
