from sqlite3 import Row

from openwpm.utilities import db_utils


def test_name_resolution(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get("http://test.localhost:8000")
    manager.close()

    results = db_utils.query_db(db, "SELECT * FROM dns_responses")
    result = results[0]
    assert isinstance(result, Row)
    assert result["used_address"] == "127.0.0.1"
    assert result["addresses"] == "127.0.0.1,::1"
    assert result["hostname"] == "test.localhost"
    assert result["canonical_name"] == "test.localhost"
