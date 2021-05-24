def test_extension_logging(task_manager_creator, default_params, tmp_path):
    test_msg = "This is a test message from the extension"
    log_path = tmp_path / "openwpm.log"
    manager_params, browser_params = default_params
    manager_params.log_path = log_path
    for browser_param in browser_params:
        browser_param.custom_params[
            "pre_instrumentation_code"
        ] = f"""
            // Weird name needed due to webpack name mangling
            _loggingdb_js__WEBPACK_IMPORTED_MODULE_1__.logWarn("{test_msg}"); 
        """

    task_manager, _ = task_manager_creator((manager_params, browser_params))
    task_manager.close()
    log_list = []
    with open(log_path, "r") as log_file:
        for log_line in log_file:
            if test_msg in log_line:
                log_list.append(log_line)
    # We expect to see it once when printing the config and once when printing the log message
    assert len(log_list) == 2 * manager_params.num_browsers
