# This is code adapted from KU Leuven crawler code written by
# Gunes Acar and Marc Juarez

import os
import time
from glob import glob


def tmp_sqlite_files_exist(path):
    """Check if temporary sqlite files(wal, shm) exist in a given path."""
    return glob(os.path.join(path, '*-wal')) or \
        glob(os.path.join(path, '*-shm'))


def sleep_until_sqlite_checkpoint(profile_dir, timeout=60):
    """
    We wait until all the shm and wal files are checkpointed to DB.
    https://www.sqlite.org/wal.html#ckpt.
    """
    while (timeout > 0 and tmp_sqlite_files_exist(profile_dir)):
        time.sleep(1)
        timeout -= 1
    print("Waited for %s seconds for sqlite checkpointing" % (60 - timeout))
