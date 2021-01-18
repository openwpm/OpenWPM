from openwpm.utilities import db_utils

from .utilities import BASE_TEST_URL

TEST_FILE = "canvas_fingerprinting.html"
TEST_URL = BASE_TEST_URL + "/" + TEST_FILE


def test_command_duration(default_params, task_manager_creator):
    manager, db = task_manager_creator(default_params)
    manager.get(url=TEST_URL, sleep=5)
    manager.close()

    get_command = db_utils.query_db(
        db,
        "SELECT duration FROM crawl_history WHERE command = 'GetCommand'",
        as_tuple=True,
    )[0]

    assert get_command[0] > (5 * 1000)  # milliseconds conversion for sleep time
    assert get_command[0] <= (
        (5 * 1000) + 2 * 1000
    )  # milliseconds conversion for sleep time + time duration a command took (milliseconds)
