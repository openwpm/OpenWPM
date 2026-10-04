from functools import partial
from typing import List, Tuple

from openwpm.command_sequence import CommandSequence
from openwpm.storage.storage_controller import INVALID_VISIT_ID
from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls


def test_local_callbacks(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """Test the storage controller as well as the entire callback machinery
    to see if all callbacks get correctly called"""
    manager, _ = task_manager_creator(default_params)
    TEST_SITE = server.base + "/simple_a.html"

    def callback(argument: List[int], success: bool) -> None:
        argument.extend([1, 2, 3])

    my_list: List[int] = []
    sequence = CommandSequence(
        TEST_SITE, blocking=True, callback=partial(callback, my_list)
    )
    sequence.get()

    manager.execute_command_sequence(sequence)
    manager.close()
    assert my_list == [1, 2, 3]


def test_clean_crawl_completes_every_visit_once(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.http_instrument = True
    manager, db = task_manager_creator((manager_params, browser_params))

    handle = manager.storage_controller_handle
    get_new_completed_visits = handle.get_new_completed_visits
    completions: List[Tuple[int, bool]] = []

    def recording_get_new_completed_visits() -> List[Tuple[int, bool]]:
        visits = get_new_completed_visits()
        completions.extend(visits)
        return visits

    handle.get_new_completed_visits = recording_get_new_completed_visits  # type: ignore[method-assign]

    callbacks: List[bool] = []
    sites = ["simple_a.html", "simple_b.html", "simple_c.html"]
    for site in sites:
        sequence = CommandSequence(f"{server.base}/{site}", callback=callbacks.append)
        sequence.get()
        manager.execute_command_sequence(sequence)
    manager.close()
    # Entries enqueued during shutdown are never read by the TaskManager.
    completions.extend(get_new_completed_visits())

    assert callbacks == [True] * len(sites)
    assert db_utils.query_db(db, "SELECT * FROM incomplete_visits") == []
    visit_ids = [
        row[0]
        for row in db_utils.query_db(
            db, "SELECT visit_id FROM site_visits", as_tuple=True
        )
    ]
    visit_completions = [c for c in completions if c[0] != INVALID_VISIT_ID]
    assert sorted(visit_completions) == sorted((v, True) for v in visit_ids)
    finalize_rows = db_utils.query_db(
        db,
        "SELECT visit_id FROM crawl_history WHERE command = 'FinalizeCommand'"
        " AND command_status = 'ok'",
        as_tuple=True,
    )
    assert sorted(row[0] for row in finalize_rows) == sorted(visit_ids)
