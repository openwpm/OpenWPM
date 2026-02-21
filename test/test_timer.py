from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls

TEST_FILE = "canvas_fingerprinting.html"


def test_command_duration(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    TEST_URL = server.base + "/" + TEST_FILE
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
