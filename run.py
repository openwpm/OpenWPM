from pathlib import Path

from utils.parsing import extract_base_domain
from openwpm.commands.browser_commands import GetCommand, BrowseCommand
from openwpm.command_sequence import CommandSequence
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager
from openwpm.storage.leveldb import LevelDbProvider
from openwpm.stealth.commands import (SetResolution, SetPosition)

import sys
import time
from datetime import date

# ENSURE TO RUN
# export DISPLAY=:0
# sudo Xorg :0 &

initial_time = time.time()
NUM_BROWSERS = 1
TIMEOUT_DURATION = 4 * 60 * 60
sites_file = None
if sys.argv[1] == 'iffys':
    sites_file = './iffys.txt'
elif sys.argv[1] == 'newsguard':
    sites_file = './newsguard.txt'

with open(sites_file, 'r') as f:
    sites = f.read().split(",")


manager_params = ManagerParams(num_browsers=NUM_BROWSERS)
browser_params = [BrowserParams(display_mode="native") for _ in range(NUM_BROWSERS)]

for browser_param in browser_params:
    browser_param.http_instrument = True
    browser_param.donottrack = False
    browser_param.cookie_instrument = True
    browser_param.navigation_instrument = True
    browser_param.stealth_js_instrument = True
    browser_param.disable_flash = False
    #browser_param.callstack_instrument = True
    browser_param.save_content = "script"
    browser_param.save_all_content = True
    browser_param.save_javascript = True
    browser_param.headless = False
    browser_param.tp_cookies = "always"
    browser_param.bot_mitigation = True

curr_date = date.today()
storage_file = "./datadir/" + str(curr_date) + "_stealth_" + sys.argv[1] + ".sqlite"
leveldb_file = "./datadir/" + str(curr_date) + "_stealth_" + sys.argv[1] +  ".ldb"

manager_params.data_directory = Path("./datadir/")
manager_params.log_path = Path("./datadir/openwpm.log")

sqlite = SQLiteStorageProvider(Path(storage_file))
leveldb = LevelDbProvider(Path(leveldb_file))

manager = TaskManager(
    manager_params,
    browser_params,
    sqlite,
    leveldb
)
task_start_time = time.time()

start_time = time.time()

for index, site in enumerate(sites):
    elapsed_time = time.time() - initial_time
    if elapsed_time > TIMEOUT_DURATION:
        print(f"Timeout reached. Exiting after {elapsed_time / 60:.2f} minutes.")
        break

    start_time = time.time()
    print("now visit: %s" % site )

    command_sequence = CommandSequence(site, site_rank=index)
    command_sequence.append_command(SetResolution(width=1600, height=800), timeout=10)
    command_sequence.append_command(SetPosition(x=50, y=200), timeout=10)

    manager.execute_command_sequence(command_sequence)

print("--- %s seconds to finish the whole task ---" % ( time.time() - task_start_time))
manager.close()
print("--- %s mins to finish the whole task ---" % ( (time.time() - initial_time) / 60))
