import datetime
import glob
import os
import subprocess
import tarfile

# Library for managing profile folders (for now, profile folder I/O)

# dumps a profile currently stored in <browser_profile_folder> to <new_folder> in which both folders are absolute paths
# profile dumped as a timestamped tar file, format is DDMMYY_HHMMSS.tar.gz
def dump_profile(browser_profile_folder, tar_location):
    # ensures that folder paths end with slashes
    browser_profile_folder = browser_profile_folder if browser_profile_folder.endswith("/") else browser_profile_folder + "/"
    tar_location = tar_location if tar_location.endswith("/") else tar_location + "/"

    if not os.path.exists(tar_location):
        os.makedirs(tar_location)

    tar = tarfile.open(tar_location + 'profile.tar.gz', 'w:gz')
    for db in ["cookies.sqlite", "cookies.sqlite-shm", "cookies.sqlite-wal",
               "places.sqlite", "places.sqlite-shm", "places.sqlite-wal"]:
        if os.path.isfile(browser_profile_folder + db):
            tar.add(browser_profile_folder + db, arcname=db)
    tar.close()

# loads a zipped profile stored in <tar_location> and unzips it in <browser_profile_folder>
# when <prof> is None, load the most recent profile in <tar_location>, other loads the profile tar <prof>
def load_profile(browser_profile_folder, tar_location):
    # ensures that folder paths end with slashes
    browser_profile_folder = browser_profile_folder if browser_profile_folder.endswith("/") else browser_profile_folder + "/"
    tar_location = tar_location if tar_location.endswith("/") else tar_location + "/"

    tar_file = tar_location + 'profile.tar.gz'

    subprocess.call(["cp", tar_file, browser_profile_folder])

    opener, mode = tarfile.open, 'r:gz'
    f = opener(browser_profile_folder + 'profile.tar.gz', mode)
    f.extractall(browser_profile_folder)
    f.close()
