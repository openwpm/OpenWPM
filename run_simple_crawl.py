from automation import TaskManager
import sys

# Runs a basic crawl which simply runs through a list of websites

# loads a list of websites from a text file
def load_sites(site_path):
    sites = []

    f = open(site_path)
    for site in f:
        cleaned_site = site.strip() if site.strip().startswith("http") else "http://" + site.strip()
        sites.append(cleaned_site)
    f.close()

    return sites

# runs the crawl itself
# <db_loc> is the absolute path of where we want to dump the database
# <db_name> is the name of the database
# <preferences> is a dictionary of preferences to initialize the crawler
def run_site_crawl(db_loc, db_name, sites, preferences):
    db_loc = db_loc if db_loc.endswith("/") else db_loc + "/"

    manager = TaskManager.TaskManager(db_loc, db_name, browser=preferences["browser"], timeout=preferences["timeout"],
                                      headless=preferences["headless"], proxy=preferences["proxy"], 
                                      tp_cookies=preferences["tp_cookies"], fourthparty=preferences["fourthparty"],
                                      donottrack=preferences["donottrack"], profile_tar=preferences["load_folder"],
                                      random_attributes=True)

    for site in sites:
        manager.get(site)
        if preferences["wipe"]:
            manager.reset()

    # dump profile at the end if necessary
    if preferences['dump_folder'] is not None:
        manager.dump_profile(preferences['dump_folder'])

    manager.close()

# prints out the help message in the case that too few arguments are mentioned
def print_help_message():
    print "\nMust call simple crawl script with at least two arguments: \n" \
          "1. The absolute directory path in which to store the crawl DB\n" \
          "2. The name of the crawl DB\n" \
          "Other command line argument flags are:\n" \
          "-browser: specifies type of browser to use (firefox or chrome)\n" \
          "-fourthparty: True/False value as to whether to use Fourthparty instrumentation\n" \
          "-donottrack: True/False value as to whether to use the Do Not Track flag\n" \
          "-tp_cookies: string designating third-party cookie preferences: always, never or just_visted\n" \
          "-proxy: True/False value as to whether to use proxy-based instrumentation\n" \
          "-headless: True/False value as to whether to run browser in headless mode\n" \
          "-timeout: timeout (in seconds) for the TaskManager to default time out loads\n" \
          "-load: absolute path of folder that contains tar-zipped user profile\n" \
          "-dump: absolute path of folder in which to dump tar-zipped user profile\n" \
          "-wipe: True/False value as to whether we want to wipe the state between sites\n"

# main helper function, reads command-line arguments and launches crawl
def main(argv):
    # filters out bad arguments
    if len(argv) < 4 or len(argv) % 2 != 0:
        print_help_message()
        return

    db_loc = argv[1]  # absolute path for the database
    db_name = argv[2]  # name of the crawl database
    site_file = argv[3]  # absolute path of the file that contains the list of sites to visit
    sites = load_sites(site_file)

    # default preferences for the crawl (see print_help_message for details of their meanings)
    preferences = {
        "browser": "firefox",
        "fourthparty": False,
        "donottrack": False,
        "tp_cookies": "always",
        "proxy": True,
        "headless": False,
        "timeout": 60.0,
        "load_folder": None,
        "dump_folder": None,
        "wipe": False
    }

    # overwrites the default preferences based on command-line inputs
    for i in xrange(4, len(argv), 2):
        if argv[i] == "-browser":
            preferences["browser"] = "chrome" if argv[i+1].lower() == "chrome" else "firefox"
        elif argv[i] == "-fourthparty":
            preferences["fourthparty"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-donottrack":
            preferences["donottrack"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-tp_cookies":
            preferences["tp_cookies"] = argv[i+1].lower()
        elif argv[i] == "-proxy":
            preferences["proxy"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-headless":
            preferences["headless"] = True if argv[i+1].lower() == "true" else False
        elif argv[i] == "-timeout":
            preferences["timeout"] = float(argv[i+1]) if float(argv[i]) > 0 else 30.0
        elif argv[i] == "-load":
            preferences["load_folder"] = argv[i+1]
        elif argv[i] == "-dump":
            preferences["dump_folder"] = argv[i+1]
        elif argv[i] == "-wipe":
            preferences["wipe"] = True if argv[i+1].lower() == "true" else False

    # launches the crawl with the updated preferences
    run_site_crawl(db_loc, db_name, sites, preferences)

# Full main function (just passes down sys.argv)
if __name__ == "__main__":
    main(sys.argv)
