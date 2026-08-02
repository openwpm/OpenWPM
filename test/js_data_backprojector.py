"""Project stealth ``javascript`` rows back into the legacy row shape.

Counterpart of :mod:`openwpm.utilities.js_settings_migrator`. Where the migrator
maps a legacy *config* forward (old -> new, browser-assisted), this back-projector
maps captured *data* backward (new -> old, pure in-process Python) so that the
legacy JS-instrument assertions in :mod:`test.test_js_instrument` can be reused
verbatim as an oracle for the stealth instrument.

Scope: **dropping the ``receiver`` column, and nothing else.**

``receiver`` (``openwpm/storage/schema.sql``) is the only column the stealth
instrument writes that the legacy schema has no counterpart for. Every other
oracle-visible column -- ``symbol``, ``operation``, ``value``, ``arguments``,
``document_url``, ``top_level_url`` -- is produced identically:

* ``symbol`` is built as ``instrumentedName + "." + propertyName`` by both
  instruments (``Extension/src/stealth/instrument.ts`` vs
  ``Extension/src/lib/js-instruments.ts``), and the migrator preserves
  the legacy dotted path as ``instrumentedName``
  (``openwpm/utilities/js_settings_migrator.py``).
* ``document_url`` / ``top_level_url`` are set by the *shared* background handler
  (``Extension/src/background/javascript-instrument.ts``) -- literally the
  same code path, so they cannot diverge.

Because ``_check_calls`` reads only named columns, dropping ``receiver`` is
provably a no-op for the oracle. The projection exists so that the rows handed to
the reused legacy assertions are honestly *legacy-shaped*, not so that any
comparison is made more tolerant.

Not normalized
--------------

These divergences are left in the data, because normalizing them would
fabricate or hide rows:

* Shared-prototype symbols. Stealth reports
  ``symbol = "<owner>.<member>"`` with the leaf interface in ``receiver``; the
  legacy leaf path cannot be rebuilt from that pair.
* Extra flat ``get`` rows where legacy recursion descended instead.
* Shared-prototype over-capture when the migrator unions
  ``receiverInterfaces`` across leaves; filter by ``(symbol, receiver)`` in
  post-processing.
"""

from typing import Any, Dict, Iterable, List, Mapping

#: The one stealth-only column with no legacy counterpart.
STEALTH_ONLY_COLUMNS = ("receiver",)


def stealth_rows_to_legacy(
    rows: Iterable[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Project stealth ``javascript`` rows into legacy-shaped rows.

    Parameters
    ----------
    rows:
        Stealth ``javascript`` rows as returned by
        ``db_utils.get_javascript_entries(db, all_columns=True)`` -- any mapping
        exposing ``keys()`` (``sqlite3.Row`` and ``dict`` both qualify).

    Returns
    -------
    A list of plain ``dict`` rows with :data:`STEALTH_ONLY_COLUMNS` removed. No
    other transformation is applied; see the module docstring.
    """
    projected: List[Dict[str, Any]] = []
    for row in rows:
        # Shallow-copy so the caller's rows are never mutated. Works for both
        # ``sqlite3.Row`` and ``dict``.
        out = {key: row[key] for key in row.keys()}
        for column in STEALTH_ONLY_COLUMNS:
            out.pop(column, None)
        projected.append(out)
    return projected
