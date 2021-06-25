# Platform Architecture

## TaskManager

### Overview

The user-facing component of the OpenWPM platform is the Task Manager.
The Task Manager oversees multiple browser instances and passes them commands.
The Task Manager also ensures that crawls continue despite browser crashes for freezes.
In particular, it checks whether a given browser fails to complete a command within a given timeout (or has died) and
kills/restarts this browser as necessary.

### Watchdogs

In OpenWPM we have a watchdog thread that tries to ensure two things.

- `process_watchdog`
  - It is part of default manager_params. It is set to false by default which can manually be set to true.
  - It is used to create another thread that kills off `GeckoDriver` (or `Xvfb`) instances that aren't currently controlled by OpenWPM.
      (GeckoDriver is used by Selenium to control Firefox and Xvfb is a "virtual display" we use to simulate having graphics when running on a server).
- `memory_watchdog`
  - It is part of default manager_params. It is set to false by default which can manually be set to true.
  - It is a watchdog that tries to ensure that no Firefox instance takes up too much memory.
  - It is mostly useful for long running cloud crawls.

### Issuing commands

OpenWPM uses the `CommandSequence` as a fundamental unit of work.
A `CommandSequence` describes as series of steps that will execute in order on a particular browser.
All available Commands are visible by inspecting the `CommandSequence` API.

For example you could wire up a `CommandSequence` to go to a given url and take a screenshot of it by writing:

```python
    command_sequence = CommandSequence(url)
    # Start by visiting the page
    command_sequence.get(sleep=3, timeout=60)
    command_sequence.save_screenshot()
```

But this on its own would do nothing, because `CommandSequence`s are not automatically scheduled.
Instead, you need to submit them to a `TaskManager` by calling:

```python
    manager.execute_command_sequence(command_sequence)
    manager.close()
```

Please note that you need to close the manager, because by default `CommandSequence`s are executed in a non-blocking fashion meaning that you might reach the end of your main function/file before the CommandSequence completed running.

`TaskManager.execute_command_sequence` has an optional `index` parameter that enables the user to specify which of the existing browsers should execute a command. The options are

- `None`: the command is executed by a browser on a first-come, first-serve basis
- `<index>`: the command is executed by the `<index>`th browser instance

### Adding new commands

Have a look at [`custom_command.py`](../custom_command.py)

## Browser Manager

### Overview

Contained in `openwpm/BrowserManager.py`, Browser Managers provide a wrapper around the drivers used to automate full browser instances. In particular, we opted to use [Selenium](http://docs.seleniumhq.org/) to drive full browser instances as bot detection frameworks can more easily detect lightweight alternatives such as PhantomJS.

Browser Managers receive the commands in a CommandSequence from the Task Manager one by one, calling the `execute`
method on each of them and stopping if one command should fail.
Browser Managers also receive browser parameters which they use to instantiate the Selenium web driver using one of
the browser initialization functions contained in `openwpm/deploy_browsers`.

The BrowserManagerHandle class, contained in the same file, is the Task Manager's wrapper around Browser Managers,
which allow it to cleanly kill and restart Browser Managers as necessary.

**Important Programming Note** The Browser Managers are designed to isolate the Task Manager from the underlying browser
instances. As part of this approach, no data from the browsers should flow up to the Task Manager
(beyond basic metadata such as the browsers' process IDs). For instance, if the Browser Manager is assigned the task of
collecting and parsing XPath data, this parsing should be completed by Browser Managers
and **not** passed up to the Task Manager for post-processing.

### Browser Information Logging

Throughout the course of a measurement, the Browser Managers' commands (along with timestamps and the status of the commands)
are logged by the Task Manager, which contributes to the reproducibility of individual experiments.
The data is sent to the Storage Controller process,
which provides stability in logging data despite the possibility of individual browser crashes.

## The WebExtension

All of our data collection happens in the OpenWPM WebExtension, which can be found under [Extension](../Extension).
The Extension makes heavy use of priviliged APIs and can only be installed on unbranded or custom builds of Firefox with add-on security disabled.

The currently supported instruments can be found in [Configuration.md](Configuration.md#Instruments)

## Data Aggregator

### Overview

One of the Data Aggregators, contained in `openwpm/DataAggregator`, gets spawned in a separate process and receives data from the WebExtension and the platform alike. We as previously mentioned we support both local as well as remote data saving.
The most useful feature of the Data Aggregator is the fact that it is isolated from the other processes through a network socket interface (see `openwpm/SocketInterface.py`).

### Data Logged

The full schema for the platform's output is contained in the [schema documentation](Schema-Documentation.md)
