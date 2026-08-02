"""Project stealth ``javascript`` rows back into the legacy row shape.

Counterpart of :mod:`openwpm.utilities.js_settings_migrator`. Where the migrator
maps a legacy *config* forward (old -> new, browser-assisted), this back-projector
maps captured *data* backward (new -> old, pure in-process Python) so that the
legacy JS-instrument assertions in :mod:`test.test_js_instrument` can be reused
verbatim as an oracle for the stealth instrument.

Scope: **dropping the ``receiver`` column, and nothing else.**

``receiver`` (``openwpm/storage/schema.sql:153``) is the only column the stealth
instrument writes that the legacy schema has no counterpart for. Every other
oracle-visible column -- ``symbol``, ``operation``, ``value``, ``arguments``,
``document_url``, ``top_level_url`` -- is produced identically:

* ``symbol`` is built as ``instrumentedName + "." + propertyName`` by both
  instruments (``Extension/src/stealth/instrument.ts:1219`` vs
  ``Extension/src/lib/js-instruments.ts:519,595,674``), and the migrator preserves
  the legacy dotted path as ``instrumentedName``
  (``openwpm/utilities/js_settings_migrator.py:318,365``).
* ``document_url`` / ``top_level_url`` are set by the *shared* background handler
  (``Extension/src/background/javascript-instrument.ts:61-64``) -- literally the
  same code path, so they cannot diverge.

Because ``_check_calls`` reads only named columns, dropping ``receiver`` is
provably a no-op for the oracle. The projection exists so that the rows handed to
the reused legacy assertions are honestly *legacy-shaped*, not so that any
comparison is made more tolerant.

LATENT, DELIBERATELY NOT IMPLEMENTED
------------------------------------
Three divergences from ``datadir/objective2-parametric-plan.md`` are known but are
**not** normalized here, and must not be normalized to turn a test green:

* **D2** -- shared-prototype symbol remap. Stealth reports
  ``symbol = "<owner>.<member>"`` (interface-level) with the leaf interface in
  ``receiver``. The legacy leaf path is *not* reconstructable from that pair, so
  synthesizing one would fabricate data. No current test config reaches it.
* **D3** -- extra flat ``get`` rows where legacy recursion descended instead.
  Unverified, and widening the expected set to absorb it would be defanging.
* **D8** -- shared-prototype over-capture, where the migrator unions
  ``receiverInterfaces`` across leaves. The migrator's own message
  (``js_settings_migrator.py:930-950``) names the correct remedy: filter results by
  ``(symbol, receiver)`` in post-processing. That is a *product* feature with real
  value, and is open owner decision 3 in the plan (section 3.4); it is out of scope
  for the parametric scaffolding and is why this module currently lives under
  ``test/`` rather than ``openwpm/utilities/``.

Adding any normalization beyond ``receiver`` requires an explicit owner sign-off
line in the plan (anti-defang gate 3, section 3.5) -- it is not a code-review-level
decision.
"""

from typing import Any, Dict, Iterable, List, Mapping

#: The one stealth-only column with no legacy counterpart (D1).
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
