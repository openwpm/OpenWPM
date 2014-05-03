from automation import TaskManager
import time
import sys
import os

# loads a list of websites from a text file
def load_sites(site_path):
    sites = []

    f = open(site_path)
    for site in f:
        cleaned_site = site.strip() if site.strip().startswith("http") else "http://" + site.strip()
        sites.append(cleaned_site)
    f.close()

    return sites

db_loc = os.path.expanduser('~/Desktop/')
db_name = 'alexa500.sqlite'

sites = load_sites('alexa500.txt')

manager = TaskManager.TaskManager(db_loc, db_name, browser='firefox', timeout=60,
                                  headless=True, proxy=True)

for site in sites:
    start_time = time.time()
    manager.get(site)
    manager.dump_storage_vectors(site, start_time)

manager.dump_profile(os.path.expanduser('~/Desktop/alexa500_05-02_profile/'), close_webdriver=True, overwrite_timeout=120)
import ipdb; ipdb.set_trace()
manager.close()
