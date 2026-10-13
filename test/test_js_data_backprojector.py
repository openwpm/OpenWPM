"""Unit tests for the stealth -> legacy row back-projection.

These are the anti-defang guard rails for :mod:`test.js_data_backprojector`.
The projection is deliberately almost a no-op: it drops the stealth-only
``receiver`` column and touches nothing else. That "nothing else" is the load
bearing property -- it is what lets the legacy assertions be reused verbatim as
an oracle for the stealth instrument without being made more tolerant. So these
tests assert the *absence* of transformation at least as hard as its presence.
"""

import sqlite3

import pytest

from test.js_data_backprojector import STEALTH_ONLY_COLUMNS, stealth_rows_to_legacy

pytestmark = pytest.mark.pyonly

# A stealth row carrying every column the legacy oracle reads, plus ``receiver``.
_STEALTH_ROW = {
    "symbol": "window.document.cookie",
    "operation": "get",
    "value": "a=1",
    "arguments": None,
    "document_url": "http://localtest.me:8000/test_pages/x.html",
    "top_level_url": "http://localtest.me:8000/test_pages/x.html",
    "receiver": "HTMLDocument",
}


def test_drops_receiver() -> None:
    (row,) = stealth_rows_to_legacy([_STEALTH_ROW])
    assert "receiver" not in row


def test_preserves_every_other_column_verbatim() -> None:
    """The oracle-visible columns must survive byte-for-byte.

    If this ever needs relaxing, the projection has started normalizing data and
    the suite is no longer the legacy oracle.
    """
    (row,) = stealth_rows_to_legacy([_STEALTH_ROW])
    expected = {k: v for k, v in _STEALTH_ROW.items() if k not in STEALTH_ONLY_COLUMNS}
    assert row == expected


def test_does_not_mutate_the_caller_rows() -> None:
    source = dict(_STEALTH_ROW)
    stealth_rows_to_legacy([source])
    assert source == _STEALTH_ROW, "back-projection mutated its input"


def test_accepts_sqlite3_row() -> None:
    """``db_utils.get_javascript_entries`` hands back ``sqlite3.Row``, not dict."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.row_factory = sqlite3.Row
        columns = ", ".join(_STEALTH_ROW)
        placeholders = ", ".join("?" * len(_STEALTH_ROW))
        conn.execute(f"CREATE TABLE javascript ({columns})")
        conn.execute(
            f"INSERT INTO javascript ({columns}) VALUES ({placeholders})",
            tuple(_STEALTH_ROW.values()),
        )
        rows = conn.execute(f"SELECT {columns} FROM javascript").fetchall()
        (row,) = stealth_rows_to_legacy(rows)
    finally:
        conn.close()
    assert row == {k: v for k, v in _STEALTH_ROW.items() if k != "receiver"}


def test_row_without_receiver_is_passed_through() -> None:
    """A legacy-shaped row must survive the projection untouched (idempotence)."""
    legacy_row = {k: v for k, v in _STEALTH_ROW.items() if k != "receiver"}
    (row,) = stealth_rows_to_legacy([legacy_row])
    assert row == legacy_row


def test_preserves_row_order_and_count() -> None:
    """No filtering, deduplication or reordering -- those would all be defangs."""
    rows = [dict(_STEALTH_ROW, value=str(i)) for i in range(5)]
    projected = stealth_rows_to_legacy(rows)
    assert [r["value"] for r in projected] == [str(i) for i in range(5)]


def test_duplicate_rows_are_not_collapsed() -> None:
    """Legacy assertions count occurrences; collapsing duplicates would hide loss."""
    projected = stealth_rows_to_legacy([_STEALTH_ROW, _STEALTH_ROW])
    assert len(projected) == 2


def test_empty_input() -> None:
    assert stealth_rows_to_legacy([]) == []


def test_receiver_is_the_only_dropped_column() -> None:
    """Guards the scope contract: widening this tuple is a defang, not a fix."""
    assert STEALTH_ONLY_COLUMNS == ("receiver",)
