## Overview

In this section, we present three basic development demos for working on the OpenWPM platform. In the first, we show how to run a basic crawl from scratch. In the second, we show how to add a new command to the platform. In the third, we provide a small example of data analysis that can be performed on the platform

## Running a simple crawl

Have a look at [demo.py](../demo.py)
Generally, measurement crawls should be able to be run using scripts with lengths on the order of 100 lines of code.
Even within this short script, there are several different options that a user can change.

Users can change the settings for task manager and individual browsers so that, for instance, certain browsers can run headless while others do not. We provide a method to read the default configuration settings into a dictionaries that can be passed to the `TaskManager` instance. Note that browser configuration is **per-browser**, so this command will return a list of dictionaries.

`manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)`

## Adding a new command

OpenWPM commands exist as part of a command sequence object, which allows one to string together a sequence of actions for a browser to take and deploy that sequence to the first available browser from the manager. Adding a command to a `CommandSequence` object will cause the browser to execute it immediately after the previously added command as long as the previous command does not time out or fail.

Suppose we want to add a top-level command to cause the browser to jiggle the mouse a few times. We may want to have the browser visit a site, jiggle the mouse, and extract the links from the site.

To add a new command you need to modify the following four files:

1. Define all required paramters in a type in `automation/Commands/Types.py`  
  In our case this looks like this:
  ```python
    class JiggleCommand(BaseCommand):
        def __init__(self, num_jiggles):
            self.num_jiggles = num_jiggles

        def __repr__(self):
            return "JiggleCommand({})".format(self.num_jiggles)
  ```

2. Define the behaviour of our new command in `*_commands.py` in `automation/Commands/`,
   e.g. `browser_commands.py`.
   Feel free to add a new module within `automation/Commands/` for your own custom commands  
    In our case this looks like this:
  ```python
    from selenium.webdriver.common.action_chains import ActionChains

    def jiggle_mouse(webdriver, number_jiggles):
        for i in xrange(0, number_jiggles):
            x = random.randrange(0, 500)
            y = random.randrange(0, 500)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
  ```

3. Make our function be called when the command_sequence reaches our Command, by adding it to the
    `execute_command` function in `automation/Commands/command_executer.py`
      In our case this looks like this:
  ```python
        elif type(command) is JiggleCommand:
        browser_commands.initialize(
            webdriver=webdriver,
            number_jiggles=self.num_jiggles)
  ```

4. Lastly we change ```automation/CommandSequence.py``` by adding a `jiggle_mouse` method to the `CommandSequence`
  so we can add our command to the commands list  
  In our case this looks like this:
  ```python
    def jiggle_mouse(self, num_jiggles, timeout=60):
    """ jiggles mouse <num_jiggles> times """
    self.total_timeout += timeout
    if not self.contains_get_or_browse:
        raise CommandExecutionError("No get or browse request preceding "
                                    "the jiggle_mouse command", self)
    command = JiggleCommand(num_jiggles)
    self.commands_with_timeout.append((command, timeout))
  ```
   A timeout is given and set by default to 60 seconds. This is added to the overall sequence timeout. Finally, we check that the `CommandSequence` instance contains a `get` or a `browse` command prior to this command being added by checking `self.contains_get_or_browse`. This is necessary as it wouldn't make sense to have selenium jiggle the mouse before loading a page.



Notice that any arguments to the command are added both to the command sequence top-level method, and are then stored in the `Command` object to be serialized and sent across the process boundary between the task manager and browser manager.

Finally, the command sequence given to the Task Manager to visit a site, sleep for 10 seconds, jiggle the mouse 10 times, and takes a screenshot would look like this:

```python
site = 'http://www.example.com'

command_sequence = CommandSequence.CommandSequence(site)
command_sequence.get(sleep=10)
command_sequence.jiggle_mouse(10)
command_sequence.screenshot_full_page()

manager.execute_command_sequence(command_sequence)
```

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
print list(fp_sites)
````

The variety of data stored in OpenWPM databases (with all instrumentation enabled) allows the above script to easily be expanded into a larger study. For instance, one step would be to see which parties are the recipients of the email address. Do these recipients later place cookies containing the email? Besides the site on which the original email leak was made, on which other first parties do these recipients appear as a third party? All of these questions are answerable through OpenWPM database instances.

