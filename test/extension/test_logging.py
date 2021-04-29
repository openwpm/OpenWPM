def test_extension_logging(task_manager_creator, default_params, tmp_path):
    test_msg = "This is a test message from the extension"
    log_path = tmp_path / "openwpm.log"
    manager_params, browser_params = default_params
    manager_params.log_path = log_path
    for browser_param in browser_params:
        browser_param.extra[
            "pre_instrumentation_code"
        ] = f"""
            loggingDB.logWarn("{test_msg}");
        """

    task_manager, _ = task_manager_creator((manager_params, browser_params))
    task_manager.close()
    count = 0
    with open(log_path, "r") as log_file:
        for log_line in log_file:
            if test_msg in log_line:
                count += 1
    # We expect to see it once when printing the config and once when printing the log message
    assert count == 2 * manager_params.num_browsers
