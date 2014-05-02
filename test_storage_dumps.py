from automation import TaskManager
import time
import sys


# loads a list of websites from a text file
def load_sites(site_path):
    sites = []

    f = open(site_path)
    for site in f:
        cleaned_site = site.strip() if site.strip().startswith("http") else "http://" + site.strip()
        sites.append(cleaned_site)
    f.close()

    return sites

db_loc = '/home/sengleha/Desktop/'
db_name = 'testing_time.sqlite'

sites = load_sites('test_sites.txt')

manager = TaskManager.TaskManager(db_loc, db_name, browser='firefox', timeout=50,
                                  headless=False, proxy=False)

for site in sites:
    start_time = time.time()
    manager.get(site)
    #import ipdb; ipdb.set_trace()
    manager.dump_storage_vectors(site, start_time)

manager.close()
