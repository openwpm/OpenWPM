import logging
import tarfile
from pathlib import Path

from selenium.webdriver import Firefox

from openwpm.config import BrowserParamsInternal, ManagerParamsInternal

from ..errors import ProfileLoadError
from ..socket_interface import ClientSocket
from .types import BaseCommand
from .utils.firefox_profile import sleep_until_sqlite_checkpoint

logger = logging.getLogger("openwpm")


def dump_profile(
    browser_profile_path: Path,
    tar_path: Path,
    compress: bool,
    browser_params: BrowserParamsInternal,
) -> None:
    """Dumps a browser profile to a tar file.

    Should only be called when the browser is closed, to prevent
    database corruption in the archived profile (see section 1.2
    of https://www.sqlite.org/howtocorrupt.html).
    """
    assert browser_params.browser_id is not None

    # Creating the folders if need be
    tar_path.parent.mkdir(exist_ok=True, parents=True)

    # see if this file exists first
    # if it does, delete it before we try to save the current session
    if tar_path.exists():
        tar_path.unlink()

    # backup and tar profile
    if compress:
        tar = tarfile.open(tar_path, "w:gz", errorlevel=1)
    else:
        tar = tarfile.open(tar_path, "w", errorlevel=1)
    logger.debug(
        "BROWSER %i: Backing up full profile from %s to %s"
        % (browser_params.browser_id, browser_profile_path, tar_path)
    )

    tar.add(browser_profile_path, arcname="")
    archived_items = tar.getnames()
    tar.close()

    required_items = [
        "cookies.sqlite",  # cookies
        "places.sqlite",  # history
        "webappsstore.sqlite",  # localStorage
    ]
    for item in required_items:
        if item not in archived_items:
            logger.critical(
                "BROWSER %i: %s NOT FOUND IN profile folder"
                % (browser_params.browser_id, item)
            )
            raise RuntimeError("Profile dump not successful")


class DumpProfileCommand(BaseCommand):
    """
    Dumps a browser profile currently stored in <browser_params.profile_path> to
    <tar_path>.
    """

    def __init__(
        self, tar_path: Path, close_webdriver: bool, compress: bool = True
    ) -> None:
        self.tar_path = tar_path
        self.close_webdriver = close_webdriver
        self.compress = compress

    def __repr__(self) -> str:
        return "DumpProfileCommand({},{},{})".format(
            self.tar_path, self.close_webdriver, self.compress
        )

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        # if this is a dump on close, close the webdriver and wait for checkpoint
        if self.close_webdriver:
            webdriver.close()
            sleep_until_sqlite_checkpoint(browser_params.profile_path)

        assert browser_params.profile_path is not None
        dump_profile(
            browser_params.profile_path,
            self.tar_path,
            self.compress,
            browser_params,
        )


def load_profile(
    browser_profile_path: Path,
    browser_params: BrowserParamsInternal,
    tar_path: Path,
) -> None:
    """
    Loads a zipped cookie-based profile stored at <tar_path> and unzips
    it to <browser_profile_path>. The tar will remain unmodified.
    """
    assert browser_params.browser_id is not None
    try:
        assert tar_path.is_file()
        # Untar the loaded profile
        if tar_path.name.endswith("tar.gz"):
            f = tarfile.open(tar_path, "r:gz", errorlevel=1)
        else:
            f = tarfile.open(tar_path, "r", errorlevel=1)
        f.extractall(browser_profile_path)
        f.close()
        logger.debug("BROWSER %i: Tarfile extracted" % browser_params.browser_id)

    except Exception as ex:
        logger.critical(
            "BROWSER %i: Error: %s while attempting to load profile"
            % (browser_params.browser_id, str(ex))
        )
        raise ProfileLoadError("Profile Load not successful")
