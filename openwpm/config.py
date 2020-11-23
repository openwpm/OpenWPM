from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


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
