import os

import pytest

from openwpm.utilities import db_utils


@pytest.mark.skipif(
    "CI" not in os.environ or os.environ["CI"] == "false",
    reason="Makes remote connections",
)
def test_name_resolution(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get("http://localtest.me:8000")
    manager.close()

    result = db_utils.query_db(db, "SELECT * FROM dns_responses")
    result = result[0]
    assert result["used_address"] == "127.0.0.1"
    assert result["addresses"] == "127.0.0.1"
    assert result["hostname"] == "localtest.me"
    assert result["canonical_name"] == "localtest.me"
