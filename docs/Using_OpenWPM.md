# Using OpenWPM

## Overview

In this section, we present three basic development demos for working on the OpenWPM platform. In the first, we show how to run a basic crawl from scratch. In the second, we show how to add a new command to the platform. In the third, we provide a small example of data analysis that can be performed on the platform.

## Running a simple crawl

Have a look at [demo.py](../demo.py)
Generally, measurement crawls should be able to be run using scripts with lengths on the order of 100 lines of code.
Even within this short script, there are several options that a user can change.

Users can change the settings for task manager and individual browsers so that, for instance, certain browsers can run headless while others do not. We provide a method to read the default configuration settings into classes that can be passed to the `TaskManager` instance. Note that browser configuration is **per-browser**, so this command will return a list of `BrowserParams`.

```py
from openwpm.config import BrowserParams, ManagerParams

manager_params = ManagerParams(num_browsers=5)
browser_params = [BrowserParams() for _ in range(manager_params.num_browsers)]
```

### Loading Custom Browser or Manager configs

Users can load custom Browser and Platform/Manager configuration by writing them into a JSON file and then loading them into respective dataclasses. For example:

```py
from openwpm.config import BrowserParams, ManagerParams

with open("<custom_manager_params>.json", 'r') as f:
  manager_params = ManagerParams.from_json(f.read())

browser_params = list()
for _ in range(num_browsers):
  with open("<custom_browser_params>.json", 'r') as file:
      browser_params.append(BrowserParams.from_json(file.read()))
```

## Defining a new command

Please have a look at [`custom_command.py`](../custom_command.py). Note that custom commands must be
defined in a separate module and imported. They can't be defined within the main crawl script.
See [#837](https://github.com/openwpm/OpenWPM/issues/837).

## Running a simple analysis

Suppose that we ran the platform over some set of sites while logged into several sites while using a particular email. During the crawl, we turned on the proxy option to log HTTP traffic. One possible threat is, perhaps due to sloppy coding, the first-party leaks the user's email as plaintext over HTTP traffic. Given an OpenWPM database, the following script logs the first-party sites on which such a leakage occurs.

````python
import sqlite3 as lite

# connect to the output database
openwpm_db = "<absolute_path_to_db>"
conn = lite.connect(openwpm_db)
cur = conn.cursor()

# dummy user email and set of first-party sites on which email is leaked
user_email = "alice.bob@insecure.com"
fp_sites = set()

# scans through the database, checking for first parties on which the email is leaked
for url, top_url in cur.execute("SELECT DISTINCT h.url, v.site_url "
                                "FROM http_requests as h JOIN site_visits as v ON "
                                "h.visit_id = v.visit_id;"):
    if user_email in url and url.startswith("http:"):
        fp_sites.add(top_url)

# outputs the results
print(list(fp_sites))
````

The variety of data stored in OpenWPM databases (with all instrumentation enabled) allows the above script to easily be expanded into a larger study. For instance, one step would be to see which parties are the recipients of the email address. Do these recipients later place cookies containing the email? Besides the site on which the original email leak was made, on which other first parties do these recipients appear as a third party? All of these questions are answerable through OpenWPM database instances.
