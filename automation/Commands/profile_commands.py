import datetime
import glob
import os
import subprocess
import tarfile
import cPickle

# Library for managing profile folders (for now, profile folder I/O)

# dumps a profile currently stored in <browser_profile_folder> to <new_folder> in which both folders are absolute paths
def dump_profile(browser_profile_folder, tar_location, browser_settings = None):
    # ensures that folder paths end with slashes
    browser_profile_folder = browser_profile_folder if browser_profile_folder.endswith("/") else browser_profile_folder + "/"
    tar_location = tar_location if tar_location.endswith("/") else tar_location + "/"

    if not os.path.exists(tar_location):
        os.makedirs(tar_location)

    # see if this file exists first, if it does
    # if it does, delete it before we try to save the current session
    if os.path.isfile(tar_location + 'profile.tar.gz'):
        subprocess.call(["rm", tar_location + 'profile.tar.gz'])

    tar = tarfile.open(tar_location + 'profile.tar.gz', 'w:gz')
    for db in ["cookies.sqlite", "cookies.sqlite-shm", "cookies.sqlite-wal",
               "places.sqlite", "places.sqlite-shm", "places.sqlite-wal"]:
        if os.path.isfile(browser_profile_folder + db):
            tar.add(browser_profile_folder + db, arcname=db)
    tar.close()

    # browser_settings stores additional profile config parameters
    # e.g. screen_res, plugin sets, user_agent string
    if browser_settings is not None:
        # see if the browser_settings file exists, and if so delete
        if os.path.isfile(tar_location + 'browser_settings.p'):
            subprocess.call(["rm", tar_location + 'profile.tar.gz'])

        with open(tar_location + 'browser_settings.p', 'wb') as f:
            cPickle.dump(browser_settings, f)

# loads a zipped profile stored in <tar_location> and unzips it in <browser_profile_folder>
def load_profile(browser_profile_folder, tar_location):
    # ensures that folder paths end with slashes
    browser_profile_folder = browser_profile_folder if browser_profile_folder.endswith("/") else browser_profile_folder + "/"
    tar_location = tar_location if tar_location.endswith("/") else tar_location + "/"

    tar_file = tar_location + 'profile.tar.gz'

    # Copy and untar the loaded profile
    subprocess.call(["cp", tar_file, browser_profile_folder])
    opener, mode = tarfile.open, 'r:gz'
    f = opener(browser_profile_folder + 'profile.tar.gz', mode)
    f.extractall(browser_profile_folder)
    f.close()

    # Check for and import additional browser settings
    try:
        with open(tar_location + 'browser_settings.p', 'rb') as f:
            browser_settings = cPickle.load(f)
    except IOError:
        browser_settings = None

    return browser_settings
