import time
from threading import Thread
import logging, math, time
import subprocess, os
from watchdog.observers import Observer


# Nifty little function to prettyfi the output. Takes in a number of bytes and spits out the
# corresponding size in the largest unit it is able to convert to.

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i: int = int(math.floor(math.log(size_bytes, 1024)))
   p: float = math.pow(1024, i)
   s: float = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def total_folder_size(startup=False, debug=False, root_dir="/tmp"):
    """_summary_

    Args:
        startup (bool, optional): Runs the function on the total supplied folder. Defaults to False.
        debug (bool, optional): Useful for debugging functionality locally. Defaults to False.
        root_dir (str, optional): The root directory to check. Defaults to "/tmp".

    Returns:
        _type_: _description_
    """
    
    
    running_total: int = 0
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
            path: str = os.path.join(root_dir,file)
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

    def __init__(self, supplied_dir=None, dirsize=0):
        self.MAX_DIRSIZE = dirsize
        self.observer = Observer()
        self.dir_to_watch = supplied_dir

    def run(self) -> None:
        # Checks if the default dirsize and directory to watch were configured. If they are still the default, it exits because
        # it would essentially work identically to setting the "reset" flag in the command sequence
        if self.MAX_DIRSIZE == 0 or self.dir_to_watch is None:
            return
        
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
        
    def periodic_check(self, profile_path, obj):
        logger = logging.getLogger("openwpm")
        # 1073741824: # 1GB
        # 20971520: # 20MB - for testing purposes
        # 52428800: # 50MB
        # 73400320: # 70MB
        # 104857600: 100MB - IDEAL for 10+ browsers
        
        # Max Size before a restart expressed in bytes
        if self.MAX_DIRSIZE == 0:
            pass
        
        READABLE_MAX_DIRSIZE = convert_size(self.MAX_DIRSIZE)
        
        dirsize = int(subprocess.check_output(['du','-s', '-b', profile_path]).split()[0].decode('utf-8'))
        readable_dirsize = convert_size(dirsize)

        if dirsize < self.MAX_DIRSIZE:
        
            logger.info(f"Current browser profile directory {profile_path} size is less than {READABLE_MAX_DIRSIZE}: {readable_dirsize}")
            return False
        else:
            obj.restart_required = True
            logger.info(f"{profile_path}: Folder scheduled to be deleted and recover {readable_dirsize} of storage.")
            return True


class StorageWatchdogThread(Thread):
    """
    This is a custom implementation of the Thread subclass from the threading module
    that allows for collection of the return value. This was necessary to prevent the main
    StorageWatchdog thread from being hemmed up running each browser profile check
    in its main thread and instead, spawning separate instances and blocking each browser thread until
    the check is complete, ensuring asynchio doesnt get upset.
    """    

    def __init__(self, watchdog: StorageWatchdog, argList: list[str]):
        """_summary_

        Args:
            watchdog (StorageWatchdog): The main StorageWatchdog Object, running the main thread
            argList (list[str]):
                argList[0]: The profile_dir
                argList[1]: The BrowserManager instance
        """
        Thread.__init__(self)
        self.ret_value = None
        self.watchdog = watchdog
        self.argList = argList
    
    def run(self):
        self.ret_value = self.watchdog.periodic_check(self.argList[0], self.argList[1])

if __name__ == '__main__':
    print("---Testing the StorageWatchdog folder size function---")
    total_folder_size(startup=True, debug=True)
