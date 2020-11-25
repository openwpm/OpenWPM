import os
from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from .errors import ConfigError

BOOL_TYPE_VALIDATION_LIST = [True, False]
DISPLAY_MODE_VALIDATION_LIST = ["native", "headless", "xvfb"]
SUPPORTED_BROWSER_LIST = [
    "firefox"
]  # Using List instead of a str type to future proof the logic as OpenWPM may add support for more browsers in future
TP_COOKIES_OPTIONALS_LIST = ["always", "never", "from_visited"]
DB_EXTENSION_TYPE_LIST = [".db", ".sqlite"]
LOG_EXTENSION_TYPE_LIST = [".log"]
CONFIG_ERROR_STRING = (
    "Found {value} as value for {parameter_name} in BrowserParams. "
    "Supported values are {value_list}. Please look at "
    "docs/Configuration.md#browser-configuration-options for more information"
)
EXTENSION_ERROR_STRING = (
    "Found {extension} extension for {parameter_name} in ManagerParams "
    "supported extensions are {value_list}. Please look at "
    "docs/Configuration.md#platform-configuration-options for more information"
)  # TODO mention supported file extensions in file docs/Configuration.md#platform-configuration-options
GENERAL_ERROR_STRING = (
    "Found invalid value `{value}` for {parameter_name} in {params_type}. "
    "Please look at docs/Configuration.md for more information"
)


@dataclass_json
@dataclass
class BrowserParams:
    extension_enabled: bool = True
    cookie_instrument: bool = True
    js_instrument: bool = False
    js_instrument_settings: list = field(
        default_factory=lambda: ["collection_fingerprinting"]
    )
    http_instrument: bool = False
    navigation_instrument: bool = False
    save_content: bool = False
    callstack_instrument: bool = False
    dns_instrument: bool = False
    seed_tar: str = None
    display_mode: str = "native"
    browser: str = "firefox"
    prefs: dict = field(default_factory=dict)
    tp_cookies: str = "always"
    bot_mitigation: bool = False
    profile_archive_dir: str = None
    recovery_tar: str = None
    donottrack: str = False
    tracking_protection: bool = False


@dataclass_json
@dataclass
class ManagerParams:
    data_directory: str = "~/openwpm/"
    log_directory: str = "~/openwpm/"
    output_format: str = "local"
    database_name: str = "crawl-data.sqlite"
    log_file: str = "openwpm.log"
    failure_limit: str = None
    testing: bool = False
    s3_bucket: str = None
    s3_directory: str = None
    memory_watchdog: bool = False
    process_watchdog: bool = False


def validate_browser_params(browser_params: BrowserParams):
    if BrowserParams() == browser_params:
        return

    if browser_params.display_mode.lower() not in DISPLAY_MODE_VALIDATION_LIST:
        raise ConfigError(
            CONFIG_ERROR_STRING.format(
                value=browser_params.display_mode,
                value_list=DISPLAY_MODE_VALIDATION_LIST,
                parameter_name="display_mode",
            )
        )

    if browser_params.browser.lower() not in SUPPORTED_BROWSER_LIST:
        raise ConfigError(
            CONFIG_ERROR_STRING.format(
                value=browser_params.browser,
                value_list=SUPPORTED_BROWSER_LIST,
                parameter_name="browser",
            )
        )

    if browser_params.tp_cookies.lower() not in TP_COOKIES_OPTIONALS_LIST:
        raise ConfigError(
            CONFIG_ERROR_STRING.format(
                value=browser_params.tp_cookies,
                value_list=TP_COOKIES_OPTIONALS_LIST,
                parameter_name="tp_cookies",
            )
        )

    if browser_params["callstack_instrument"] and not browser_params["js_instrument"]:
        raise ConfigError(
            "The callstacks instrument currently doesn't work without "
            "the JS instrument enabled. see: "
            "https://github.com/mozilla/OpenWPM/issues/557"
        )


def validate_manager_params(manager_params: ManagerParams):
    if ManagerParams() == manager_params:
        return

    try:
        log_file_extension = os.path.splitext(manager_params.log_file)[1]
        if log_file_extension.lower() not in LOG_EXTENSION_TYPE_LIST:
            raise ConfigError(
                EXTENSION_ERROR_STRING.format(
                    extension=log_file_extension or "no",
                    value_list=LOG_EXTENSION_TYPE_LIST,
                    parameter_name="log_file",
                )
            )
    except TypeError:
        raise ConfigError(
            GENERAL_ERROR_STRING.format(
                value=manager_params.log_file,
                parameter_name="log_file",
                params_type="ManagerParams",
            )
        )

    try:
        database_extension = os.path.splitext(manager_params.log_directory)[1]
        if database_extension.lower() not in DB_EXTENSION_TYPE_LIST:
            raise ConfigError(
                EXTENSION_ERROR_STRING.format(
                    extension=database_extension or "no",
                    value_list=DB_EXTENSION_TYPE_LIST,
                    parameter_name="database_name",
                )
            )
    except TypeError:
        raise ConfigError(
            GENERAL_ERROR_STRING.format(
                value=manager_params.database_name,
                parameter_name="database_name",
                params_type="ManagerParams",
            )
        )
