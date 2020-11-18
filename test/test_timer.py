from ..openwpm import TaskManager
from ..openwpm.utilities import db_utils
from .openwpmtest import OpenWPMTest


class TestCommandDuration(OpenWPMTest):
    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_command_duration(self):
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(url="http://www.example.com", sleep=5)
        manager.close()

        get_command = db_utils.query_db(
            manager_params["db"],
            "SELECT duration " "FROM crawl_history ",
            as_tuple=True,
        )

        assert get_command[1][0] > (5 * 1000)  # milliseconds conversion for sleep time
        assert get_command[1][0] <= (
            (5 * 1000) + 3 * 1000
        )  # milliseconds conversion for sleep time + time duration a command took (milliseconds)
