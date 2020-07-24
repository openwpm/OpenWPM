# !!Warning!!

As of January 31st, 2017 this section is out of date and needs a complete rewrite.
DO NOT TREAT ANYTHING IN THIS FILE AS FACT UNLESS VERIFIED AGAINST THE CODE!

# TaskManager

## Overview

The user-facing component of the OpenWPM platform is the Task Manager. The Task Manager oversees multiple browser instances and passes them commands. The Task Manager also ensures that crawls continue despite browser crashes for freezes. In particular, it checks whether a given browser fails to complete a command within a given timeout (or has died) and kills/restarts this browser as necessary.

More importantly, the Task Manager supports profile maintenance throughout a measurement. In particular, it cleanly transfers cookies, history and other data between browser instances between crashes so a given browser appears to represent the same user. The Task Manager also has support to dump these browser profiles (as well as browser settings such as enabling Do Not Track) at any point during a crawl and when instantiating a new Task Manager.

## Instantiating a Task Manager

All automation code is contained within the `automation` folder; the Task Manager code is contained in `automation/TaskManager.py`.

Task Managers can be instantiated in the following way:

`manager = TaskManager.TaskManager(<db_path>, <browser_params>, <num_browsers>)`

such that, `<db_path>` is the absolute path to the output database (even if this database does not yet exist), `<browser_params>` is a list of dictionaries where each dictionary represents the parameters set for a given browser and `<num_browsers>` is the number of browsers to be instantiated.

`<task_description>` is an optional string that can be used to describe the crawl associated with a given Task Manager instance. This description is useful for record-keeping for longer studies. 

However, the power of the platform is from the variety of parameters passed in through the `<browser_params>` dictionaries. We have provided a JSON-encoded dictionary at `automation/default_settings.json`. Their meanings are contained below:

* `num_browsers`: number of browser instances the Task Manager should create and manage (takes an integer value)
* `browser`: the type of browser that the Task Manager should create ('firefox' is the primary option but 'chrome' has some support as well)
* `headless`: indicates whether the browsers should be run in headless mode, a useful option for virtual machines (takes a boolean value)
* `proxy`: indicates whether the platform should instantiate a data-logging proxy, which is necessary for most measurements (takes a boolean value)
* `donottrack`: indicates whether the browser should turn on the Do Not Track flag (takes a boolean)
* `tp_cookies`: indicates the browser policy with respect to when to allow third-party cookies (can be set to 'always', 'never' or 'from_visited')
* `disable_flash`: indicates whether the platform should disable Flash objects (takes a boolean value)
* `browser_debugging`: indicates whether the platform should turn on support for browser debugging options (takes a boolean value)
* `timeout`: sets the default time (in seconds) for Task Manager commands to be executed before restarting a browser instance
* `profile_tar`: provides the absolute path of a tar file to be loaded which contains a Firefox profile and browser settings (takes a string value or None if no loading is desired)
* `random_attributes`: indicates whether the browser should be set with random attributes in an attempt to avoid browser fingerprinting (takes a boolean value)
* `bot_mitigation`: indicates whether the platform should enable bot-mitigation techniques such as random mouse movements and window scrolling (takes a boolean value)

One useful feature of the platform leverages the `<num_browsers>` parameters. Typically, this parameter is used to verify that the number of preference dictionaries in the list `<browser_params>` is correct. However, if a user passes in a single preference dictionary, the platform will internally create `<num_browsers>` browser instances, each using this preference dictionary.

## Issuing commands

The high-level commands for the Task Manager are contained at the bottom of the Task Manager file. An example command (visiting `example.com`) is contained below:

`manager.get('http://example.com')`

These Task Manager commands are custom defined and only require the basic arguments required to execute the command. In general, these commands are designed to capture high-level logic (e.g. visit a news site and extract headlines off the page). Beyond the basic parameters, setting `overwrite_timeout` to another integer overwrites the default command timeout for that command, a useful feature for commands that are known to take a long time.

The `index` parameter enables the end-user to specify which of the many browsers execute a command. The options are

* `None`: the command is executed by a single browser on a first-come, first-serve basis
* `<index>`: the command is executed by the `<index>`th browser instance
* `'*'`: the command is sent to all browser, asynchronously
* `'**'`: the command is sent to all browsers, synchronously (useful for removing temporal effects)

## Adding new commands

The overall workflow is: 1. a user issues a command to the Task Manager 2. the Task Manager communicates these commands to the Browser Managers (which wrap around the browser) 3. the Browser Managers execute these high-level actions by passing a series of lower-level commands to the browser drivers. 

To add a new command, hooks for this command must be added in the following places:

* In `automation/TaskManager.py` a high-level command should be added at the bottom of the file in the style of the `get` command.
* In `automation/Commands/command_executor.py` a new branch condition that accepts the tuple-format of this command should be added. This branch condition should call a helper function contained somewhere in the `automation/Commands` folder or a module-specific subfolder.

# Browser Manager

## Overview

Contained in `automation/BrowserManager.py`, Browser Managers provide a wrapper around the drivers used to automate full browser instances. In particular, we opted to use [Selenium](http://docs.seleniumhq.org/) to drive full browser instances as bot detection frameworks can more easily detect lightweight alternatives such as PhantomJS. 

Browser Managers receive commands from the Task Manager, which they then pass to the command executor (located in `automation/Commands/command_executor.py`), which receives a command tuple and convert it into web driver actions. Browser Managers also receive browser parameters which they use to instantiate the Selenium web driver using one of the browser initialization functions contained in `automation/DeployBrowsers`. 

The Browser class, contained in the same file, is the Task Manager's wrapper around Browser Managers, which allow it to cleanly kill and restart Browser Managers as necessary.

**Important Programming Note** The Browser Managers are designed to isolate the Task Manager from the underlying browser instances. As part of this approach, no data from the browsers should flow up to the Task Manager (beyond basic metadata such as the browsers' process IDs). For instance, if the Browser Manager is assigned the task of collecting and parsing XPath data, this parsing should be completed by Browser Managers and **not** passed up to the Task Manager for post-processing.

## Browser Information Logging

Throughout the course of a measurement, the Browser Managers' commands (along with timestamps and the status of the commands) are logged by the Task Manager, which contributes the the reproducibility of individual experiments. Depending on whether the `proxy` flag is enabled in the Task Manager, the Browser Managers also instantiate HTTP proxies, specifically [mitmproxy](http://mitproxy.org) instances, which records traffic-related data during the crawl. The data are sent to the Data Aggregator process, which provides stability in logging data despite the possibility of individual browser crashes.

# Data Aggregator

## Overview

The Data Aggregator, contained in `automation/DataAggregator/DataAggregator.py`, is a separate process of the platform that receives data from the proxies and other instrumentation and logs the data into a SQLite database. The most useful feature of the Data Aggregator is the fact that it is isolated from the other processes through a network socket interface (see `automation/SocketInterface.py`). 

So far the platform logs a wide variety of information into a single database. We hope that these databases will be expanded and standardized so different teams of researchers can run each other's scripts on their own datasets as a means of verifying results.

## Data Logged

The full schema for the platform's output is contained in `automation/schema.sql`. On a high-level, the current information logged (assuming turning on the proxy and enabling Flash) is as follows:

* **crawl metadata**: browser options, start time, competition time
* **HTTP requests**: referrer, headers, method, timestamp, top URL (i.e. currently-visited site)
* **HTTP responses**: referrer, headers, method, status, location (for redirects), timestamp, top URL
* **HTTP cookies (both through Proxy and cookie DB scan)**: domain, name, value, expiry, accessed time
* **Adobe Flash cookies**: page URL, domain, file name, key, content
* **localStorage**: scope, value
* **crawl history**: commands, command arguments, success statuses, timestamps