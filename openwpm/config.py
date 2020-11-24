from dataclasses import dataclass, field

from dataclasses_json import dataclass_json

from .Errors import ConfigError

BOOL_TYPE_VALIDATION_LIST = [True, False]
DISPLAY_MODE_VALIDATION_LIST = ["native", "headless", "xvfb"]
SUPPORTED_BROWSER_LIST = ["firefox"]
TP_COOKIES_OPTIONALS_LIST = ["always", "never", "from_visited"]


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
            "Unrecognized value provided for BrowserParams.display_mode. "
            "Please look into BrowserParams Documentation for more information"
        )

    if browser_params.browser.lower() not in SUPPORTED_BROWSER_LIST:
        raise ConfigError(
            "Unrecognized value provided for BrowserParams.browser. "
            "Please look into BrowserParams Documentation for more information"
        )

    if browser_params.tp_cookies.lower() not in TP_COOKIES_OPTIONALS_LIST:
        raise ConfigError(
            "Unrecognized value provided for BrowserParams.tp_cookies. "
            "Please look into BrowserParams Documentation for more information"
        )

    # js_instrument_settings =? remaining
