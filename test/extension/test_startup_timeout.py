def test_extension_startup_timeout(task_manager_creator, default_params):
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.custom_params[
            "pre_instrumentation_code"
        ] = """
            const myPromise = new Promise((resolve, reject) => {
              setTimeout(() => {
                resolve();
              }, 30000); // Delaying for 30 seconds
            });
            await myPromise;
        """
    tm, _ = task_manager_creator((manager_params, browser_params))
