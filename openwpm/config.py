import os
from dataclasses import dataclass, field
from json import JSONEncoder
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from dataclasses_json import DataClassJsonMixin
from dataclasses_json import config as DCJConfig

from .errors import ConfigError
from .types import BrowserId

BOOL_TYPE_VALIDATION_LIST = [True, False]
DISPLAY_MODE_VALIDATION_LIST = ["native", "headless", "xvfb"]
SUPPORTED_BROWSER_LIST = [
    "firefox"
]  # Using List instead of a str type to future proof the logic as OpenWPM may add support for more browsers in future
TP_COOKIES_OPTIONALS_LIST = ["always", "never", "from_visited"]
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
)
GENERAL_ERROR_STRING = (
    "Found invalid value `{value}` for {parameter_name} in {params_type}. "
    "Please look at docs/Configuration.md for more information"
)

ALL_RESOURCE_TYPES = {
    "beacon",
    "csp_report",
    "font",
    "image",
    "imageset",
    "main_frame",
    "media",
    "object",
    "object_subrequest",
    "ping",
    "script",
    "stylesheet",
    "sub_frame",
    "web_manifest",
    "websocket",
    "xbl",
    "xml_dtd",
    "xmlhttprequest",
    "xslt",
    "other",
}


def str_to_path(string: Optional[str]) -> Optional[Path]:
    if string is not None:
        return Path(string)
    return None


def path_to_str(path: Optional[Path]) -> Optional[str]:
    if path is not None:
        return str(path.resolve())
    return None


@dataclass
class BrowserParams(DataClassJsonMixin):
    """
    Configuration that might differ per browser

    OpenWPM allows you to run multiple browsers with different
    configurations in parallel and this class allows you
    to customize behaviour of an individual browser
    """

    extension_enabled: bool = True
    cookie_instrument: bool = True
    js_instrument: bool = False
    js_instrument_settings: List[Union[str, dict]] = field(
        default_factory=lambda: ["collection_fingerprinting"]
    )
    http_instrument: bool = False
    navigation_instrument: bool = False
    save_content: Union[bool, str] = False
    callstack_instrument: bool = False
    dns_instrument: bool = False
    seed_tar: Optional[Path] = field(
        default=None, metadata=DCJConfig(encoder=path_to_str, decoder=str_to_path)
    )
    display_mode: Literal["native", "headless", "xvfb"] = "native"
    browser: str = "firefox"
    prefs: dict = field(default_factory=dict)
    tp_cookies: str = "always"
    bot_mitigation: bool = False
    profile_archive_dir: Optional[Path] = field(
        default=None, metadata=DCJConfig(encoder=path_to_str, decoder=str_to_path)
    )
    recovery_tar: Optional[Path] = None
    donottrack: bool = False
    tracking_protection: bool = False
    custom_params: Dict[Any, Any] = field(default_factory=lambda: {})


@dataclass
class ManagerParams(DataClassJsonMixin):
    """
    Configuration for the TaskManager
    The configuration will be the same for all browsers running on the same
    TaskManager.
    It can be used to control storage locations or which watchdogs should
    run
    """

    data_directory: Path = field(
        default=Path.home() / "openwpm",
        metadata=DCJConfig(encoder=path_to_str, decoder=str_to_path),
    )
    """The directory into which screenshots and page dumps will be saved"""
    log_path: Path = field(
        default=Path.home() / "openwpm" / "openwpm.log",
        metadata=DCJConfig(encoder=path_to_str, decoder=str_to_path),
    )
    """The path to the file in which OpenWPM will log. The
    directory given will be created if it does not exist."""
    testing: bool = False
    """A platform wide flag that can be used to only run certain functionality
    while testing. For example, the Javascript instrumentation"""
    memory_watchdog: bool = False
    """A watchdog that tries to ensure that no Firefox instance takes up too much memory.
    It is mostly useful for long running cloud crawls"""
    process_watchdog: bool = False
    """- It is used to create another thread that kills off `GeckoDriver` (or `Xvfb`) instances that haven't been spawned by OpenWPM. (GeckoDriver is used by
         Selenium to control Firefox and Xvfb a "virtual display" so we simulate having graphics when running on a server)."""
    num_browsers: int = 1
    _failure_limit: Optional[int] = None
    """- The number of command failures the platform will tolerate before raising a
        `CommandExecutionError` exception. Otherwise the default is set to 2 x the
         number of browsers plus 10. The failure counter is reset at the end of each
         successfully completed command sequence.
       - For non-blocking command sequences that cause the number of failures to
         exceed `failure_limit` the `CommandExecutionError` is raised when
         attempting to execute the next command sequence."""

    @property
    def failure_limit(self) -> int:
        if self._failure_limit is None:
            return 2 * self.num_browsers + 10
        return self._failure_limit

    @failure_limit.setter
    def failure_limit(self, value: int) -> None:
        self._failure_limit = value


@dataclass
class BrowserParamsInternal(BrowserParams):
    browser_id: Optional[BrowserId] = None
    profile_path: Optional[Path] = None
    cleaned_js_instrument_settings: Optional[List[Dict[str, Any]]] = None


@dataclass
class ManagerParamsInternal(ManagerParams):
    storage_controller_address: Optional[Tuple[str, int]] = None
    logger_address: Optional[Tuple[str, ...]] = None
    screenshot_path: Optional[Path] = field(
        default=None, metadata=DCJConfig(encoder=path_to_str, decoder=str_to_path)
    )
    source_dump_path: Optional[Path] = field(
        default=None, metadata=DCJConfig(encoder=path_to_str, decoder=str_to_path)
    )


def validate_browser_params(browser_params: BrowserParams) -> None:
    if BrowserParams() == browser_params:
        return
    try:
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

        if browser_params.callstack_instrument and not browser_params.js_instrument:
            raise ConfigError(
                "The callstacks instrument currently doesn't work without "
                "the JS instrument enabled. see: "
                "https://github.com/mozilla/OpenWPM/issues/557"
            )

        if not isinstance(browser_params.save_content, bool) and not isinstance(
            browser_params.save_content, str
        ):
            raise ConfigError(
                GENERAL_ERROR_STRING.format(
                    value=browser_params.save_content,
                    parameter_name="save_content",
                    params_type="BrowserParams",
                )
            )

        if browser_params.save_content:
            if isinstance(browser_params.save_content, str):
                configured_types = set(browser_params.save_content.split(","))
                if not configured_types.issubset(ALL_RESOURCE_TYPES):
                    diff = configured_types.difference(ALL_RESOURCE_TYPES)
                    raise ConfigError(
                        "Unrecognized resource types provided ",
                        "in browser_params.save_content (%s)" % diff,
                    )

    except:
        raise ConfigError(
            "Something went wrong while validating BrowserParams. "
            "Please check values provided for BrowserParams are of expected types"
        )


def validate_manager_params(manager_params: ManagerParams) -> None:
    if ManagerParams() == manager_params:
        return

    try:
        log_file_extension = manager_params.log_path.suffix
        if log_file_extension.lower() not in LOG_EXTENSION_TYPE_LIST:
            raise ConfigError(
                EXTENSION_ERROR_STRING.format(
                    extension=log_file_extension or "no",
                    value_list=LOG_EXTENSION_TYPE_LIST,
                    parameter_name="log_file",
                )
            )
    except (TypeError, AttributeError):
        raise ConfigError(
            GENERAL_ERROR_STRING.format(
                value=manager_params.log_path,
                parameter_name="log_file",
                params_type="ManagerParams",
            )
        )

    # This check is necessary to not cause any internal error
    if not isinstance(manager_params.failure_limit, int):
        raise ConfigError(
            GENERAL_ERROR_STRING.format(
                value=manager_params.failure_limit,
                parameter_name="failure_limit",
                params_type="ManagerParams",
            ).replace(
                "Please look at docs/Configuration.md for more information",
                "failure_limit must be of type `int` or `None`",
            )
        )


def validate_crawl_configs(
    manager_params: ManagerParams, browser_params: List[BrowserParams]
) -> None:
    validate_manager_params(manager_params)
    for bp in browser_params:
        validate_browser_params(bp)

    if len(browser_params) != manager_params.num_browsers:
        raise ConfigError(
            "Number of BrowserParams instances is not the same "
            "as manager_params.num_browsers. Make sure you are assigning number of browsers "
            "to be used to manager_params.num_browsers in your entry file"
        )


class ConfigEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj.resolve())
        return JSONEncoder.default(self, obj)
