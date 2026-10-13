"""Prototype: the stealth instrument in dedicated workers (#1245 step 2).

``stealth_worker.html`` starts ``stealth_worker.js``, which reads navigator
members, draws on an ``OffscreenCanvas`` and calls ``convertToBlob``; the page
repeats the reads and the drawing on the main thread and spawns blob:, data:,
module, nested and cross-site-frame workers.
"""

from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

from openwpm.utilities import db_utils

from .test_stealth import _collect_results, _stealth_params
from .utilities import ServerUrls

WORKER_PAGE = "/stealth_worker.html"
NATIVE_FILL_TEXT = "function fillText() {\n    [native code]\n}"

Run = Tuple[Dict[str, Any], Path]


@pytest.fixture(scope="module")
def run(xpi: None, server: ServerUrls, tmp_path_factory: pytest.TempPathFactory) -> Run:
    data_dir = tmp_path_factory.mktemp("stealth_workers")
    params = _stealth_params(data_dir)
    params[1][0].prefs["extensions.openwpm.stealthWorkers"] = True
    results = _collect_results(params, server.base + WORKER_PAGE)
    return results, data_dir / "crawl-data.sqlite"


def _rows(db_path: Path, where: str) -> list:
    return db_utils.query_db(
        db_path,
        "SELECT symbol, operation, script_url, document_url, top_level_url, "
        f"tab_id, frame_id FROM javascript WHERE {where}",
        as_tuple=True,
    )


def test_worker_records_attributed_to_page(run: Run, server: ServerUrls) -> None:
    _, db_path = run
    page = server.base + WORKER_PAGE
    script = server.base + "/stealth_worker.js"
    rows = _rows(db_path, f"script_url = '{script}'")
    seen = {(symbol, operation) for symbol, operation, *_ in rows}
    for expected in (
        ("WorkerNavigator.hardwareConcurrency", "get"),
        ("OffscreenCanvas.getContext", "call"),
        ("OffscreenCanvasRenderingContext2D.fillText", "call"),
        ("OffscreenCanvas.convertToBlob", "call"),
    ):
        assert expected in seen, f"{expected} not recorded; got {sorted(seen)}"
    for _, _, _, document_url, top_level_url, tab_id, frame_id in rows:
        assert (document_url, top_level_url, frame_id) == (page, page, 0)
        assert tab_id > 0


def test_worker_kinds_covered(run: Run, server: ServerUrls) -> None:
    results, db_path = run
    assert not any(
        str(value).startswith("error:") for value in results["coverage"].values()
    ), results["coverage"]
    scripts = {
        script_url
        for _, _, script_url, *_ in _rows(db_path, "symbol LIKE 'WorkerNavigator.%'")
    }
    assert any(url.startswith("blob:") for url in scripts), scripts
    assert any(url.startswith("data:") for url in scripts), scripts
    assert server.base + "/stealth_worker_module.js" in scripts
    # Spawned by stealth_worker_nested.js.
    assert server.base + "/stealth_worker_inner.js" in scripts


def test_cross_site_frame_worker_attributed_to_frame(
    run: Run, server: ServerUrls
) -> None:
    _, db_path = run
    frame = server.base.replace("//localhost:", "//127.0.0.1:")
    rows = _rows(db_path, f"script_url = '{frame}/stealth_worker_inner.js'")
    assert rows
    for _, _, _, document_url, top_level_url, _, frame_id in rows:
        assert document_url == frame + "/stealth_worker_frame.html"
        assert top_level_url == server.base + WORKER_PAGE
        assert frame_id != 0


def test_worker_values_match_main_thread(run: Run) -> None:
    """CreepJS compares worker values against the window's."""
    results, _ = run
    worker, main = results["worker"], results["main"]
    for key in main:
        assert worker[key] == main[key], key


def test_convert_to_blob_promise_untouched(run: Run) -> None:
    results, _ = run
    assert results["worker"]["promise"] == "true|true|0"
    # A reaction attached by the instrument would mark the rejection handled.
    assert results["worker"]["unhandledRejections"] == 1


def test_forwarder_shape_matches_native(run: Run) -> None:
    tells = run[0]["worker"]["tells"]
    assert tells["fillTextShape"] == "fillText|3|name,length|false"
    assert tells["getterShape"] == "get hardwareConcurrency|0|name,length"
    assert tells["fillTextInstanceofFunction"] is True


@pytest.mark.xfail(strict=True, reason="in-realm forwarders show their source")
def test_forwarder_to_string_matches_native(run: Run) -> None:
    assert run[0]["worker"]["tells"]["fillTextToString"] == NATIVE_FILL_TEXT


@pytest.mark.xfail(strict=True, reason="in-realm forwarders add a stack frame")
def test_no_instrument_frame_in_page_stacks(run: Run) -> None:
    assert "resource://openwpm/" not in run[0]["worker"]["tells"]["errorStack"]
