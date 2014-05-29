import os
import subprocess
import tarfile
import cPickle

from utils.firefox_profile import sleep_until_sqlite_checkpoint


def save_browser_settings(location, browser_settings):
    """
    browser_settings stores additional profile config parameters
    e.g. screen_res, plugin sets, user_agent string
    """
    if browser_settings is not None:
        # see if the browser_settings file exists, and if so delete
        if os.path.isfile(location + 'browser_settings.p'):
            subprocess.call(["rm", location + 'browser_settings.p'])

        with open(location + 'browser_settings.p', 'wb') as f:
            cPickle.dump(browser_settings, f)


def load_browser_settings(location):
    """ loads the browser settings from a pickled dictionary in <location>"""
    try:
        with open(location + 'browser_settings.p', 'rb') as f:
            browser_settings = cPickle.load(f)
    except IOError:
        browser_settings = None
    return browser_settings


def save_flash_files(dump_location):
    """
    save all files from the default flash storage locations
    NOTE: this only supports the default linux storage locations
    """
    print "Saving flash not supported yet"


def load_flash_files(tar_location):
    """ clear old flash cookies and load ones from dump """
    print "Loading flash not supported yet"


def dump_profile(browser_profile_folder, tar_location, close_webdriver, webdriver=None, browser_settings=None,
                 save_flash=False, full_profile=True):
    """
    dumps a browser profile currently stored in <browser_profile_folder> to
    <tar_location> in which both folders are absolute paths.
    if <browser_settings> exists they are also saved
    <full_profile> specifies to save the entire profile directory (not just cookies)
    <save_flash> specifies whether to dump flash files
    """

    # ensures that folder paths end with slashes
    browser_profile_folder = browser_profile_folder if browser_profile_folder.endswith("/")\
        else browser_profile_folder + "/"
    tar_location = tar_location if tar_location.endswith("/") else tar_location + "/"

    if not os.path.exists(tar_location):
        os.makedirs(tar_location)

    if full_profile:
        tar_name = 'full_profile.tar.gz'
    else:
        tar_name = 'profile.tar.gz'

    # see if this file exists first
    # if it does, delete it before we try to save the current session
    if os.path.isfile(tar_location + tar_name):
        subprocess.call(["rm", tar_location + tar_name])

    # if this is a dump on close, close the webdriver and wait for checkpoint
    if close_webdriver:
        webdriver.close()
        sleep_until_sqlite_checkpoint(browser_profile_folder)

    # backup and tar profile
    tar = tarfile.open(tar_location + tar_name, 'w:gz')
    if full_profile:  # backup all storage vectors
        storage_vector_files = [
            'cookies.sqlite', 'cookies.sqlite-shm', 'cookies.sqlite-wal',  # cookies
            'places.sqlite', 'places.sqlite-shm', 'places.sqlite-wal',  # history
            'webappsstore.sqlite', 'webappsstore.sqlite-shm', 'webappsstore.sqlite-wal',  # todo: localStorage
            # todo: '_CACHE_CLEAN_' #flag for cache
        ]
        storage_vector_dirs = [
            'webapps',  # related to localStorage?
            'storage'  # directory for IndexedDB
        ]
                # todo: 'Cache', # ff cache files - need workaround: https://support.mozilla.org/en-US/questions/945274
                # todo: 'startupCache' # related to cache?

        #Hack to force Cache to import properly -- DOESN'T WORK
        for item in storage_vector_files:
            full_path = os.path.join(browser_profile_folder, item)
            if os.path.isfile(full_path):
                tar.add(full_path, arcname=item)
        for item in storage_vector_dirs:
            full_path = os.path.join(browser_profile_folder, item)
            if os.path.isdir(full_path):
                tar.add(full_path, arcname=item)

    else:  # only backup cookies and history
        for db in ["cookies.sqlite", "cookies.sqlite-shm", "cookies.sqlite-wal",
                   "places.sqlite", "places.sqlite-shm", "places.sqlite-wal"]:
            if os.path.isfile(browser_profile_folder + db):
                tar.add(browser_profile_folder + db, arcname=db)
    tar.close()

    # save flash cookies
    if save_flash:
        save_flash_files(tar_location)
    
    # save the browser settings
    if browser_settings is not None:
        save_browser_settings(tar_location, browser_settings)


def load_profile(browser_profile_folder, tar_location, load_flash=False):
    """
    loads a zipped cookie-based profile stored in <tar_location> and
    unzips it to <browser_profile_folder>. This will load whatever profile
    is in the folder, either full_profile.tar.gz or profile.tar.gz
    """
    try:
        # ensures that folder paths end with slashes
        browser_profile_folder = browser_profile_folder if browser_profile_folder.endswith("/") \
            else browser_profile_folder + "/"
        tar_location = tar_location if tar_location.endswith("/") else tar_location + "/"

        if os.path.isfile(tar_location + 'full_profile.tar.gz'):
            tar_name = 'full_profile.tar.gz'
        else:
            tar_name = 'profile.tar.gz'

        # Copy and untar the loaded profile
        subprocess.call(["cp", tar_location + tar_name, browser_profile_folder])
        opener, mode = tarfile.open, 'r:gz'
        f = opener(browser_profile_folder + tar_name, mode)
        f.extractall(browser_profile_folder)
        f.close()
        subprocess.call(["rm", browser_profile_folder + tar_name])

        # clear and load flash cookies
        if load_flash:
            load_flash_files(tar_location)

        # load the browser settings
        browser_settings = load_browser_settings(tar_location)

    except Exception as ex:
        print "Error loading profile: ", str(ex)
        browser_settings = None

    return browser_settings
