import logging
import os
import shutil
import tarfile
from typing import Any, Dict

from selenium.webdriver import Firefox

from openwpm.config import BrowserParams, ManagerParams

from ..errors import ProfileLoadError
from ..socket_interface import ClientSocket
from .types import BaseCommand
from .utils.firefox_profile import sleep_until_sqlite_checkpoint

logger = logging.getLogger("openwpm")


class DumpProfileCommand(BaseCommand):
    """
    dumps a browser profile currently stored in <browser_profile_folder> to
    <tar_location> in which both folders are absolute paths.
    """

    def __init__(self, dump_folder, close_webdriver, compress):
        self.dump_folder = dump_folder
        self.close_webdriver = close_webdriver
        self.compress = compress

    def __repr__(self):
        return "DumpProfCommand({},{},{})".format(
            self.dump_folder, self.close_webdriver, self.compress
        )

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        logger.debug(
            "BROWSER %i: Profile dumping is currently unsupported. "
            "See: https://github.com/mozilla/OpenWPM/projects/2."
            % browser_params.browser_id
        )
        return
        browser_profile_folder = browser_params.profile_path

        # ensures that folder paths end with slashes
        if browser_profile_folder[-1] != "/":
            browser_profile_folder = browser_profile_folder + "/"
        if tar_location[-1] != "/":
            tar_location = tar_location + "/"

        if not os.path.exists(tar_location):
            os.makedirs(tar_location)

        if compress:
            tar_name = "profile.tar.gz"
        else:
            tar_name = "profile.tar"

        # see if this file exists first
        # if it does, delete it before we try to save the current session
        if os.path.isfile(tar_location + tar_name):
            os.remove(tar_location + tar_name)

        # if this is a dump on close, close the webdriver and wait for checkpoint
        if close_webdriver:
            webdriver.close()
            sleep_until_sqlite_checkpoint(browser_profile_folder)

        # backup and tar profile
        if compress:
            tar = tarfile.open(tar_location + tar_name, "w:gz", errorlevel=1)
        else:
            tar = tarfile.open(tar_location + tar_name, "w", errorlevel=1)
        logger.debug(
            "BROWSER %i: Backing up full profile from %s to %s"
            % (
                browser_params.browser_id,
                browser_profile_folder,
                tar_location + tar_name,
            )
        )
        storage_vector_files = [
            "cookies.sqlite",  # cookies
            "cookies.sqlite-shm",
            "cookies.sqlite-wal",
            "places.sqlite",  # history
            "places.sqlite-shm",
            "places.sqlite-wal",
            "webappsstore.sqlite",  # localStorage
            "webappsstore.sqlite-shm",
            "webappsstore.sqlite-wal",
        ]
        storage_vector_dirs = [
            "webapps",  # related to localStorage?
            "storage",  # directory for IndexedDB
        ]
        for item in storage_vector_files:
            full_path = os.path.join(browser_profile_folder, item)
            if (
                not os.path.isfile(full_path)
                and full_path[-3:] != "shm"
                and full_path[-3:] != "wal"
            ):
                logger.critical(
                    "BROWSER %i: %s NOT FOUND IN profile folder, skipping."
                    % (browser_params.browser_id, full_path)
                )
            elif not os.path.isfile(full_path) and (
                full_path[-3:] == "shm" or full_path[-3:] == "wal"
            ):
                continue  # These are just checkpoint files
            tar.add(full_path, arcname=item)
        for item in storage_vector_dirs:
            full_path = os.path.join(browser_profile_folder, item)
            if not os.path.isdir(full_path):
                logger.warning(
                    "BROWSER %i: %s NOT FOUND IN profile folder, skipping."
                    % (browser_params.browser_id, full_path)
                )
                continue
            tar.add(full_path, arcname=item)
        tar.close()


def load_profile(browser_profile_folder, manager_params, browser_params, tar_location):
    """
    loads a zipped cookie-based profile stored in <tar_location> and
    unzips it to <browser_profile_folder>. This will load whatever profile
    is in the folder, either full_profile.tar.gz or profile.tar.gz
    """
    try:
        # ensures that folder paths end with slashes
        if browser_profile_folder[-1] != "/":
            browser_profile_folder = browser_profile_folder + "/"
        if tar_location[-1] != "/":
            tar_location = tar_location + "/"

        if os.path.isfile(tar_location + "profile.tar.gz"):
            tar_name = "profile.tar.gz"
        else:
            tar_name = "profile.tar"

        # Copy and untar the loaded profile
        logger.debug(
            "BROWSER %i: Copying profile tar from %s to %s"
            % (
                browser_params.browser_id,
                tar_location + tar_name,
                browser_profile_folder,
            )
        )
        shutil.copy(tar_location + tar_name, browser_profile_folder)

        if tar_name == "profile.tar.gz":
            f = tarfile.open(browser_profile_folder + tar_name, "r:gz", errorlevel=1)
        else:
            f = tarfile.open(browser_profile_folder + tar_name, "r", errorlevel=1)
        f.extractall(browser_profile_folder)
        f.close()
        os.remove(browser_profile_folder + tar_name)
        logger.debug("BROWSER %i: Tarfile extracted" % browser_params.browser_id)

    except Exception as ex:
        logger.critical(
            "BROWSER %i: Error: %s while attempting to load profile"
            % (browser_params.browser_id, str(ex))
        )
        raise ProfileLoadError("Profile Load not successful")
