import pytest

from openwpm.errors import BrowserConfigError


def test_extension_startup_timeout(task_manager_creator, default_params):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
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
    with pytest.raises(BrowserConfigError) as error:
        tm, _ = task_manager_creator((manager_params, browser_params[:1]))

    assert error.value.message == "The extension did not boot up in time"
