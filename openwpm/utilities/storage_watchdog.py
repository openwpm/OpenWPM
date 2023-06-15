import time
import logging, math, time
import subprocess, os
from watchdog.observers import Observer


# Nifty little function to prettyfi the output. Takes in a number of bytes and spits out the
# corresponding size in the largest unit it is able to convert to.
def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def total_folder_size(startup=False, debug=False, root_dir="/tmp"):
    
    running_total = 0
    if not startup:
        for file in os.listdir(root_dir):
            if "firefox" in file or ".xpi" in file or "owpm" in file or "Temp" in file:
                path = os.path.join(root_dir,file)
                try:
                    running_total += int(subprocess.check_output(['du','-s', '-b', path]).split()[0].decode('utf-8'))
                except:
                    pass
        if debug:
            print(f"Currently using: {convert_size(running_total)} of storage on disk...")
            return
        return (f"Currently using: {convert_size(running_total)} of storage on disk...")
    else:
        for file in os.listdir(root_dir):
            path = os.path.join(root_dir,file)
            try:
                running_total += int(subprocess.check_output(['du','-s', '-b', path], stderr=subprocess.DEVNULL).split()[0].decode('utf-8'))
            except:
                pass
        if debug:
            print(f"Readable files in {root_dir} folder take up {convert_size(running_total)} of storage on disk at start time...")
            return
        return (f"Readable files in {root_dir} folder take up {convert_size(running_total)} of storage on disk at start time...")

class StorageWatchdog():
    # DIRECTORY_TO_WATCH = "/mnt/04dc803b-5e97-4b16-bdaf-80845c61942d"

    def __init__(self):
        self.observer = Observer()

    def run(self) -> None:
        logger = logging.getLogger("openwpm")
        logger.info("Starting the StorageWatchdog...")
        logger.info(total_folder_size(startup=True))
        try:
            while True:
                time.sleep(300) # Give storage updates every 5 minutes
                logger.info(total_folder_size())
                
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


def start_storage_watchdog():
    w = StorageWatchdog()
    w.run()

def periodic_check(profile_path, obj):
    logger = logging.getLogger("openwpm")
    # 1073741824: # 1GB
    # 20971520: # 20MB - for testing purposes
    # 52428800: # 50MB
    # 73400320: # 70MB
    # 104857600: 100MB - IDEAL for 10+ browsers
    
    # Max Size before a restart expressed in bytes
    MAX_DIRSIZE = 104857600 
    READABLE_MAX_DIRSIZE = convert_size(MAX_DIRSIZE)
    
    dirsize = int(subprocess.check_output(['du','-s', '-b', profile_path]).split()[0].decode('utf-8'))
    readable_dirsize = convert_size(dirsize)

    if dirsize < MAX_DIRSIZE:  # 100MB
    
        logger.info(f"Current browser profile directory {profile_path} size is less than {READABLE_MAX_DIRSIZE}: {readable_dirsize}")
        return False
    else:
        obj.restart_required = True
        logger.info(f"{profile_path}: Folder scheduled to be deleted and recovered {readable_dirsize} of storage.")
        return True

if __name__ == '__main__':

    total_folder_size(startup=True, debug=True)
