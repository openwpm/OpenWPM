from automation import TaskManager
import sys
import json
import os

# Runs a basic crawl which simply runs through a list of websites


def load_sites(site_path):
    """ loads a list of websites from a text file """
    sites = []

    f = open(site_path)
    for site in f:
        cleaned_site = site.strip() if site.strip().startswith("http") else "http://" + site.strip()
        sites.append(cleaned_site)
    f.close()

    return sites


def run_site_crawl(db_path, sites, preferences, dump_location):
    """
    runs the crawl itself
    <db_path> is the absolute path of crawl database
    <preferences> is a dictionary of preferences to initialize the crawler
    """
    manager = TaskManager.TaskManager(db_path, preferences, 1)

    for site in sites:
        manager.get(site)

    if dump_location:
        manager.dump_profile(dump_location,True)

    manager.close()


def print_help_message():
    """ prints out the help message in the case that too few arguments are mentioned """
    print "\nMust call simple crawl script with at least one arguments: \n" \
          "The absolute directory path of the new crawl DB\n" \
          "Other command line argument flags are:\n" \
          "-browser: specifies type of browser to use (firefox or chrome)\n" \
          "-donottrack: True/False value as to whether to use the Do Not Track flag\n" \
          "-tp_cookies: string designating third-party cookie preferences: always, never or just_visted\n" \
          "-proxy: True/False value as to whether to use proxy-based instrumentation\n" \
          "-headless: True/False value as to whether to run browser in headless mode\n" \
          "-timeout: timeout (in seconds) for the TaskManager to default time out loads\n" \
          "-profile_tar: absolute path of folder in which to load tar-zipped user profile\n" \
          "-dump_location: absolute path of folder in which to dump tar-zipped user profile\n" \
          "-bot_mitigation: True/False value as to whether to enable bot-mitigation measures"


def main(argv):
    """ main helper function, reads command-line arguments and launches crawl """

    # filters out bad arguments
    if len(argv) < 3 or len(argv) % 2 == 0:
        print_help_message()
        return

    db_path = argv[1]  # absolute path for the database
    site_file = argv[2]  # absolute path of the file that contains the list of sites to visit
    sites = load_sites(site_file)

    # loads up the default preference dictionary
    fp = open(os.path.join(os.path.dirname(__file__), 'automation/default_settings.json'))
    preferences = json.load(fp)
    fp.close()

    dump_location = None
    # overwrites the default preferences based on command-line inputs
    for i in xrange(3, len(argv), 2):
        if argv[i] == "-browser":
            preferences["browser"] = "chrome" if argv[i+1].lower() == "chrome" else "firefox"
        elif argv[i] == "-donottrack":
            preferences["donottrack"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-tp_cookies":
            preferences["tp_cookies"] = argv[i+1].lower()
        elif argv[i] == "-proxy":
            preferences["proxy"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-headless":
            preferences["headless"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-bot_mitigation":
            preferences["bot_mitigation"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-timeout":
            preferences["timeout"] = float(argv[i+1]) if float(argv[i]) > 0 else 30.0
        elif argv[i] == "-profile_tar":
            preferences["profile_tar"] = argv[i+1]
        elif argv[i] == "-disable_flash":
            preferences["disable_flash"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-dump_location":
            dump_location = argv[i+1]

    # launches the crawl with the updated preferences
    run_site_crawl(db_path, sites, preferences, dump_location)

if __name__ == "__main__":
    main(sys.argv)
