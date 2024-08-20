import logging
import math
import os
import time
from pathlib import Path
from threading import Thread
from typing import Optional

# Nifty little function to prettyfi the output. Takes in a number of bytes and spits out the
# corresponding size in the largest unit it is able to convert to.


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i: int = int(math.floor(math.log(size_bytes, 1024)))
    p: float = math.pow(1024, i)
    s: float = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def total_folder_size(startup: bool = False, root_dir: str = "/tmp") -> str:
    """Generates a human-readable message about the current size of the directory

    Args:
        startup (bool, optional): Runs the function on the total supplied folder.
        root_dir (str, optional): The root directory that will be recursively checked.
    """

    running_total: int = 0
    if not startup:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for file in filenames:
                if (
                    "firefox" in file
                    or ".xpi" in file
                    or "owpm" in file
                    or "Temp" in file
                ):
                    path = os.path.join(dirpath, file)
                    # skip if it is symbolic link
                    if not os.path.islink(path):
                        running_total += os.path.getsize(path)
        return f"Currently using: {convert_size(running_total)} of storage on disk..."

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            path = os.path.join(dirpath, file)
            # skip if it is symbolic link
            if not os.path.islink(path):
                running_total += os.path.getsize(path)
    return f"Readable files in {root_dir} folder take up {convert_size(running_total)} of storage on disk at start time..."


class StorageLogger(Thread):
    """Logs the total amount of storage used in the supplied_dir"""

    def __init__(self, supplied_dir: Optional[Path] = None) -> None:
        super().__init__()
        self.dir_to_watch = supplied_dir

    def run(self) -> None:
        logger = logging.getLogger("openwpm")
        # Checks if the default dirsize and directory to watch were configured.
        # If they are still the default, it exits because
        # it would essentially work identically to setting the "reset" flag in the command sequence
        if self.dir_to_watch is None:
            logger.info("No dir_to_watch specified. StorageLogger shutting down")
            return

        logger.info("Starting the StorageLogger...")
        logger.info(total_folder_size(startup=True))
        try:
            while True:
                time.sleep(300)  # Give storage updates every 5 minutes
                logger.info(total_folder_size())
        except:
            print("Error")


def profile_size_exceeds_max_size(
    profile_path: Path,
    max_dir_size: int,
) -> bool:
    logger = logging.getLogger("openwpm")
    # 1073741824: # 1GB
    # 20971520: # 20MB - for testing purposes
    # 52428800: # 50MB
    # 73400320: # 70MB
    # 104857600: 100MB - IDEAL for 10+ browsers

    readable_max_dir_size = convert_size(max_dir_size)

    dir_size = 0
    for dirpath, dirnames, filenames in os.walk(profile_path):
        for file in filenames:
            path = os.path.join(dirpath, file)
            # skip if it is symbolic link
            if not os.path.islink(path):
                dir_size += os.path.getsize(path)

    readable_dir_size = convert_size(dir_size)

    if dir_size < max_dir_size:
        logger.info(
            f"Current browser profile directory {profile_path} size is less than {readable_max_dir_size}: {readable_dir_size}"
        )
        return False
    else:
        logger.info(
            f"{profile_path}: Folder scheduled to be deleted and recover {readable_dir_size} of storage."
        )
        return True


if __name__ == "__main__":
    print("---Testing the StorageWatchdog folder size function---")
    print(total_folder_size(startup=True))
