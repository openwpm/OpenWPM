# A collection of file utilities

import os
import shutil


def rmsubtree(location):
    """Clears all subfolders and files in location"""
    for root, dirs, files in os.walk(location):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
