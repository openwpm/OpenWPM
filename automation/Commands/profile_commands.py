
import logging
import os
import pickle
import shutil
import tarfile

from ..Errors import ProfileLoadError
from .utils.file_utils import rmsubtree
from .utils.firefox_profile import sleep_until_sqlite_checkpoint

# Flash Plugin Storage Location -- Linux ONLY
HOME = os.path.expanduser('~')
FLASH_LOCS = [
    HOME + '/.macromedia/Flash_Player/#SharedObjects',
    HOME + '/.macromedia/Flash_Player/macromedia.com/support/flashplayer/sys'
]
logger = logging.getLogger('openwpm')


def save_browser_settings(location, browser_settings):
    """
    browser_settings stores additional profile config parameters
    e.g. screen_res, plugin sets, user_agent string
    """
    if browser_settings is not None:
        # see if the browser_settings file exists, and if so delete
        if os.path.isfile(location + 'browser_settings.p'):
            os.remove(location + 'browser_settings.p')

        with open(location + 'browser_settings.p', 'wb') as f:
            pickle.dump(browser_settings, f)


def load_browser_settings(location):
    """ loads the browser settings from a pickled dictionary in <location>"""
    try:
        with open(location + 'browser_settings.p', 'rb') as f:
            browser_settings = pickle.load(f)
    except IOError:
        browser_settings = None
    return browser_settings


def save_flash_files(browser_params, dump_location, clear=False):
    """
    save all files from the default flash storage locations
    clear: sets whether to clear storage locations after backup
    """
    if not os.path.isdir(dump_location):
        os.makedirs(dump_location)

    # Copy all flash objects over to dump location
    for location in FLASH_LOCS:
        if not os.path.isdir(location):
            logger.warning("BROWSER %i: %s not found when attempting to save "
                           "flash files, skipping..." %
                           (browser_params['crawl_id'], location))
            continue

        logger.debug("BROWSER %i: SAVING %s during flash file archive" %
                     (browser_params['crawl_id'], location))
        (head, tail) = os.path.split(location)

        # Remove old backups if exist
        if os.path.exists(os.path.join(dump_location, tail)):
            shutil.rmtree(os.path.join(dump_location, tail))

        # Make new backups
        shutil.copytree(location, os.path.join(dump_location, tail))

        if clear:
            logger.debug("BROWSER %i: CLEARING %s during flash file archive" %
                         (browser_params['crawl_id'], location))
            rmsubtree(location)


def load_flash_files(browser_params, tar_location):
    """ clear old flash cookies and load ones from dump """
    # Clear previous objects prior to loading
    for location in FLASH_LOCS:
        if not os.path.isdir(location):
            logger.warning("BROWSER %i: %s not found when attempting to load "
                           "flash files, skipping..." %
                           (browser_params['crawl_id'], location))
            continue

        logger.debug("BROWSER %i: CLEARING %s before loading flash files" %
                     (browser_params['crawl_id'], location))
        shutil.rmtree(location)

        # Copy flash storage objects from tar_location
        (head, tail) = os.path.split(location)
        if os.path.exists(os.path.join(tar_location, tail)):
            shutil.copytree(os.path.join(tar_location, tail), location)
        else:
            logger.warning(
                "BROWSER %i: %s not found while loading flash "
                "files, skipping..." %
                (browser_params['crawl_id'], os.path.join(tar_location, tail)))
            continue


def dump_profile(browser_profile_folder, manager_params, browser_params,
                 tar_location, close_webdriver, webdriver=None,
                 browser_settings=None, save_flash=False, compress=False):
    """
    dumps a browser profile currently stored in <browser_profile_folder> to
    <tar_location> in which both folders are absolute paths.
    if <browser_settings> exists they are also saved
    <save_flash> specifies whether to dump flash files
    """
    logger.debug("BROWSER %i: Profile dumping is currently unsupported. "
                 "See: https://github.com/mozilla/OpenWPM/projects/2." %
                 browser_params['crawl_id'])
    return

    # ensures that folder paths end with slashes
    if browser_profile_folder[-1] != '/':
        browser_profile_folder = browser_profile_folder + "/"
    if tar_location[-1] != '/':
        tar_location = tar_location + "/"

    if not os.path.exists(tar_location):
        os.makedirs(tar_location)

    if compress:
        tar_name = 'profile.tar.gz'
    else:
        tar_name = 'profile.tar'

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
        tar = tarfile.open(tar_location + tar_name, 'w:gz', errorlevel=1)
    else:
        tar = tarfile.open(tar_location + tar_name, 'w', errorlevel=1)
    logger.debug(
        "BROWSER %i: Backing up full profile from %s to %s" %
        (browser_params['crawl_id'], browser_profile_folder,
         tar_location + tar_name)
    )
    storage_vector_files = [
        'cookies.sqlite',  # cookies
        'cookies.sqlite-shm',
        'cookies.sqlite-wal',
        'places.sqlite',  # history
        'places.sqlite-shm',
        'places.sqlite-wal',
        'webappsstore.sqlite',  # localStorage
        'webappsstore.sqlite-shm',
        'webappsstore.sqlite-wal',
    ]
    storage_vector_dirs = [
        'webapps',  # related to localStorage?
        'storage'  # directory for IndexedDB
    ]
    for item in storage_vector_files:
        full_path = os.path.join(browser_profile_folder, item)
        if not os.path.isfile(full_path) and \
                full_path[-3:] != 'shm' and \
                full_path[-3:] != 'wal':
            logger.critical(
                "BROWSER %i: %s NOT FOUND IN profile folder, skipping." %
                (browser_params['crawl_id'], full_path))
        elif not os.path.isfile(full_path) and \
                (full_path[-3:] == 'shm' or full_path[-3:] == 'wal'):
            continue  # These are just checkpoint files
        tar.add(full_path, arcname=item)
    for item in storage_vector_dirs:
        full_path = os.path.join(browser_profile_folder, item)
        if not os.path.isdir(full_path):
            logger.warning(
                "BROWSER %i: %s NOT FOUND IN profile folder, skipping." %
                (browser_params['crawl_id'], full_path))
            continue
        tar.add(full_path, arcname=item)
    tar.close()

    # save flash cookies
    if save_flash:
        save_flash_files(browser_params, tar_location)

    # save the browser settings
    if browser_settings is not None:
        save_browser_settings(tar_location, browser_settings)


def load_profile(browser_profile_folder, manager_params, browser_params,
                 tar_location, load_flash=False):
    """
    loads a zipped cookie-based profile stored in <tar_location> and
    unzips it to <browser_profile_folder>. This will load whatever profile
    is in the folder, either full_profile.tar.gz or profile.tar.gz
    """
    try:
        # ensures that folder paths end with slashes
        if browser_profile_folder[-1] != '/':
            browser_profile_folder = browser_profile_folder + "/"
        if tar_location[-1] != '/':
            tar_location = tar_location + "/"

        if os.path.isfile(tar_location + 'profile.tar.gz'):
            tar_name = 'profile.tar.gz'
        else:
            tar_name = 'profile.tar'

        # Copy and untar the loaded profile
        logger.debug(
            "BROWSER %i: Copying profile tar from %s to %s" %
            (browser_params['crawl_id'], tar_location + tar_name,
             browser_profile_folder)
        )
        shutil.copy(tar_location + tar_name, browser_profile_folder)

        if tar_name == 'profile.tar.gz':
            f = tarfile.open(browser_profile_folder + tar_name, 'r:gz',
                             errorlevel=1)
        else:
            f = tarfile.open(browser_profile_folder + tar_name, 'r',
                             errorlevel=1)
        f.extractall(browser_profile_folder)
        f.close()
        os.remove(browser_profile_folder + tar_name)
        logger.debug(
            "BROWSER %i: Tarfile extracted" % browser_params['crawl_id'])

        # clear and load flash cookies
        if load_flash:
            load_flash_files(browser_params, tar_location)

        # load the browser settings
        browser_settings = load_browser_settings(tar_location)
    except Exception as ex:
        logger.critical(
            "BROWSER %i: Error: %s while attempting to load profile" %
            (browser_params['crawl_id'], str(ex)))
        raise ProfileLoadError('Profile Load not successful')

    return browser_settings
