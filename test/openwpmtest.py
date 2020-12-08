import logging
import os
from abc import ABCMeta, abstractmethod
from os.path import isfile, join
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from openwpm import task_manager
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SqlLiteStorageProvider

from . import utilities

NUM_BROWSERS = 2


@pytest.mark.usefixtures("xpi", "server")
class OpenWPMTest:
    @pytest.fixture(autouse=True)
    def set_tmpdir(self, tmpdir):
        """Create a tmpdir fixture to be used in `get_test_config`.

        Based on:
        https://mail.python.org/pipermail/pytest-dev/2014-April/002484.html
        """
        self.tmpdir = tmpdir

    def get_config(self, data_dir) -> Tuple[ManagerParams, List[BrowserParams]]:
        pass

    def visit(self, page_url, data_dir="", sleep_after=0):
        """Visit a test page with the given parameters."""
        manager_params, browser_params = self.get_config(data_dir)
        structured_provider = SqlLiteStorageProvider(manager_params["db"])
        manager = task_manager.TaskManager(
            manager_params, browser_params, structured_provider, None
        )
        if not page_url.startswith("http"):
            page_url = utilities.BASE_TEST_URL + page_url
        manager.get(url=page_url, sleep=sleep_after)
        manager.close()
        return manager_params.database_name

    def get_test_config(
        self,
        data_dir: Optional[Path] = None,
        num_browsers: int = NUM_BROWSERS,
        display_mode: str = "headless",
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        """Load and return the default test parameters."""
        if not data_dir:
            data_dir = self.tmpdir
        assert data_dir is not None  # Mypy doesn't understand this without help
        manager_params = ManagerParams(num_browsers=num_browsers)
        browser_params = [BrowserParams() for _ in range(num_browsers)]
        manager_params.data_directory = data_dir
        manager_params.log_directory = data_dir
        manager_params.num_browsers = num_browsers
        for i in range(num_browsers):
            browser_params[i].display_mode = display_mode
        manager_params.database_name = (
            manager_params.data_directory / manager_params.database_name
        )

        return manager_params, browser_params
