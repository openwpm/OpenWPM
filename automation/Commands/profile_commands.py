import datetime
import glob
import os
import subprocess
import tarfile

# Library for managing profile folders (for now, profile folder I/O)

# dumps a profile currently stored in <profile_folder> to <new_folder> in which both folders are absolute paths
# profile dumped as a timestamped tar file, format is DDMMYY_HHMMSS.tar.gz
def dump_profile(profile_folder, new_folder):
    # ensures that folder paths end with slashes
    profile_folder = profile_folder if profile_folder.endswith("/") else profile_folder + "/"
    new_folder = new_folder if new_folder.endswith("/") else new_folder + "/"

    if not os.path.exists(new_folder):
        os.makedirs(new_folder)

    tar = tarfile.open(new_folder + 'profile.tar.gz', 'w:gz')
    for db in ["cookies.sqlite", "cookies.sqlite-shm", "cookies.sqlite-wal",
               "places.sqlite", "places.sqlite-shm", "places.sqlite-wal"]:
        if os.path.isfile(profile_folder + db):
            tar.add(profile_folder + db, arcname=db)
    tar.close()

# loads a zipped profile stored in <old_folder> and unzips it in <profile_folder>
# when <prof> is None, load the most recent profile in <old_folder>, other loads the profile tar <prof>
def load_profile(profile_folder, old_folder, prof=None):
    # ensures that folder paths end with slashes
    profile_folder = profile_folder if profile_folder.endswith("/") else profile_folder + "/"
    old_folder = old_folder if old_folder.endswith("/") else old_folder + "/"

    if prof is None:  # gets the most recent profile
        files = glob.glob(old_folder + '*.tar.gz')
        files.sort(key=os.path.getmtime, reverse=True)

        subprocess.call(["cp", files[0], profile_folder])
        archive_filename = os.path.basename(files[0])

        opener, mode = tarfile.open, 'r:gz'
        f = opener(profile_folder + archive_filename, mode)
        f.extractall(profile_folder)
        f.close()
   
    else:  # load the user specified tar file
        archive_filename = old_folder + prof
        subprocess.call(["cp", archive_filename, profile_folder])
        opener, mode = tarfile.open, 'r:gz'
        f = opener(profile_folder + prof, mode)
        f.extractall(profile_folder)
        f.close()
