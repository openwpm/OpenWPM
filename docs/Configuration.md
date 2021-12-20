# Browser and Platform Configuration

The browser and platform can be configured by two separate classes. The
platform configuration options can be set in `manager_params`, while the
browser configuration options can be set in `browser_params`. The default
settings are given in `openwpm/config.py` in class `BrowserParams` and `ManagerParams`

To load the default configuration create instances of `config::ManagerParams` and `config::BrowserParams`. For example:

```python
from openwpm.config import BrowserParams, ManagerParams

manager_params = ManagerParams(num_browsers=5)
browser_params = [BrowserParams() for _ in range(manager_params.num_browsers)]
```

where `manager_params` is of type `class<ManagerParams>` and `browser_params` is a length 5 list
of configurations of `class<BrowserParams>`.

- [Browser and Platform Configuration](#browser-and-platform-configuration)
  - [Platform Configuration Options](#platform-configuration-options)
  - [Browser Configuration Options](#browser-configuration-options)
  - [Validations](#validations)
  - [Instruments](#instruments)
    - [`http_instrument`](#http_instrument)
    - [`js_instrument`](#js_instrument)
    - [`navigation_instrument`](#navigation_instrument)
    - [`callstack_instrument`](#callstack_instrument)
    - [`dns_instrument`](#dns_instrument)
    - [`cookie_instrument`](#cookie_instrument)
  - [Browser Profile Support](#browser-profile-support)
    - [Stateful vs Stateless crawls](#stateful-vs-stateless-crawls)
    - [Loading and saving a browser profile](#loading-and-saving-a-browser-profile)
      - [Save a profile](#save-a-profile)
      - [Load a profile](#load-a-profile)
  - [Non instrument data gathering](#non-instrument-data-gathering)
    - [Log Files](#log-files)
    - [Browser Profile](#browser-profile)
    - [Rendered Page Source](#rendered-page-source)
    - [Screenshots](#screenshots)
    - [`save_content`](#save_content)


<!--- ## Platform Configuration Options -->

## Browser Configuration Options

Note: Instrumentation configuration options are described in the
*Instruments* section and profile configuration options are
described in the *Browser Profile Support* section. As such, these options are
left out of this section.

- `bot_mitigation`
  - Performs some actions to prevent the platform from being detected as a bot.
  - Note, these aren't comprehensive and automated interaction with the site
    will still appear very bot-like.
- `display_mode`:
  - `native`:
    - Launch the browser normally - GUI will be visible
  - `headless`:
    - Launch the browser in headless mode (supported as of Firefox 56),
        no GUI will be visible.
    - Use this when running browsers on a remote machine or to run crawls in the
        background on a local machine.
  - `xvfb`:
    - Launch the browser using the X virtual frame buffer. In this mode, Firefox
      is not running in its own headless mode, but no GUI will be displayed.
    - This mode requires `Xvfb` to be on your path. On Ubuntu that is achieved by running
      `sudo apt-get install xvfb`. For other platforms check [www.X.org](http://www.X.org).
  - `headless` mode and `xvfb` are not equivalent. `xvfb` is a full browser, but you get
    "headless" browsing because you do not need to be in a full X environment e.g. on a
    server. `headless` mode is supported on all platforms and is implemented by the browser
    but has some differences. For example WebGL is not supported in headless mode.
    <https://github.com/openwpm/OpenWPM/issues/448> discusses additional factors to consider
    when picking a `display_mode`.
- `browser`
  - Used to specify which browser to launch. Currently, only `firefox` is
    supported.
  - Other browsers may be added in the future.
- `tp_cookies`
  - Specifies the third-party cookie policy to set in Firefox.
  - The following options are supported:
    - `always`: Accept all third-party cookies
    - `never`: Never accept any third-party cookies
    - `from_visited`: Only accept third-party cookies from sites that have been visited as a first party.
- `donottrack`
  - Set to `True` to enable Do Not Track in the browser.
- `tracking_protection`
  - **NOT SUPPORTED.** See [#101](https://github.com/citp/OpenWPM/issues/101).
  - Set to `True` to enable Firefox's built-in
    [Tracking Protection](https://developer.mozilla.org/en-US/Firefox/Privacy/Tracking_Protection).

## Validations

To validate `browser_params` and `manager_params`, we have two methods, one for each type of params: `config::validate_browser_params` and `config::validate_manager_params`. For example:

```python
from openwpm.config import (
  validate_browser_params,
  validate_manager_params,
  validate_crawl_configs,
)

for bp in browser_params:
  validate_browser_params(bp)
validate_manager_params(manager_params)
validate_crawl_configs(manager_params, browser_params)
```

**NOTE**: If any validations fail, we raise `ConfigError`

## Instruments

Instruments are the core of the data collection infrastructure that OpenWPM provides.
They allow collecting various types of data that is labeled per visit and aim to capture as
much of a website's behaviour as we can.

If you feel that we are missing a fundamental instrument and are willing to implement it,
please [file an issue](https://github.com/openwpm/OpenWPM/issues/new?labels=feature-request),
and we'll try to assist you in writing that instrument.

Below you'll find a description for every single instrument, however if you
want to just look at the output schema look [here](Schema-Documentation.md)

To activate a given instrument set `browser_params[i].instrument_name = True`

### `http_instrument`

- HTTP Request and Response Headers, redirects, and POST request bodies
- Data is saved to the `http_requests`, `http_responses`, and `http_redirects` tables.
  - `http_requests` schema
        [documentation](Schema-Documentation.md#http-requests)
  - `channel_id` can be used to link a request saved in the
        `http_requests` table to its corresponding response in the
        `http_responses` table.
  - `channel_id` can also be used to link a request to the subsequent
        request that results after an HTTP redirect (3XX response). Use the
        `http_redirects` table, which includes a mapping between
        `old_channel_id`, the `channel_id` of the HTTP request that
        resulted in a 3XX response, and `new_channel_id`, the HTTP request
        that resulted from that redirect.
        TODO: `channel_id`s are now persisted across redirects
- OCSP POST request bodies are not recorded
- Note: request and response headers for cached content are also saved,
    except for images.
    See: [Bug 634073](https://bugzilla.mozilla.org/show_bug.cgi?id=634073).

### `js_instrument`

- Records all method calls (with arguments) and property accesses for configured APIs
- Configure `browser_params.js_instrument_settings` to desired settings.
- Data is saved to the `javascript` table.
- The full specification for `js_instrument_settings` is defined by a JSON schema.
  Details of that schema are available in [docs/schemas/README.md](../docs/schemas/README.md).
  In summary, a list is passed with JS objects to be instrumented and details about how
  that object should be instrumented. The js_instrument_settings you pass to browser_params
  will be validated python side against the JSON schema before the crawl starts running.
- A number of shortcuts are available to make writing `js_instrument_settings` less
  cumbersome than spelling out the full schema. These shortcuts are converted to a full
  specification by the `clean_js_instrumentation_settings` method in
  [openwpm/js_instrumentation.py](../openwpm/js_instrumentation.py).
- The first shortcut is the fingerprinting collection, specified by
  `collection_fingerprinting`. This was the default prior to v0.11.0. It contains a collection
  of APIs of potential fingerprinting interest:
  - HTML5 Canvas
  - HTML5 WebRTC
  - HTML5 Audio
  - Plugin access (via `navigator.plugins`)
  - MIMEType access (via `navigator.mimeTypes`)
  - `window.Storage`, `window.localStorage`, `window.sessionStorage`,
          and `window.name` access.
  - Navigator properties (e.g. `appCodeName`, `oscpu`, `userAgent`, ...)
  - Window properties (via `window.screen`)
- `collection_fingerprinting` is the default if `js_instrument` is `True`.
- The fingerprinting collection is specified by the json file
  [fingerprinting.json](../openwpm/js_instrumentation_collections/fingerprinting.json).
  This file is also a nice reference example for specifying your own APIs using the other
  shortcuts.
- Shortcuts:
  - Specifying just a string will instrument
      the whole API with the [default log settings](../docs/schemas/js_instrument_settings-settings-objects-properties-log-settings.md)
  - For just strings you can specify a [Web API](https://developer.mozilla.org/en-US/docs/Web/API)
      such as `XMLHttpRequest`. Or you can specify instances on window e.g. `window.document`.
  - Alternatively, you can specify a single-key dictionary that maps an API name to the properties / settings you'd
      like to use. The key of this dictionary can be an instance on `window` or a Web API.
      The value of this dictionary can be:
    - A list - this is a shortcut for `propertiesToInstrument` (see [log settings](../docs/schemas/js_instrument_settings-settings-objects-properties-log-settings.md))
    - A dictionary - with non default log settings. Items missing from this dictionary
          will be filled in with the default log settings.
  - Here are some examples:

      ```json
      // Collections
      "collection_fingerprinting",
      // APIs, with or without settings details
      "Storage",
      "XMLHttpRequest",
      {"XMLHttpRequest": {"excludedProperties": ["send"]}},
      // APIs with shortcut to includedProperties
      {"Prop1": ["hi"], "Prop2": ["hi2"]},
      {"XMLHttpRequest": ["send"]},
      // Specific instances on window
      {"window.document": ["cookie", "referrer"]},
      {"window": ["name", "localStorage", "sessionStorage"]}
      ```

  - Note, the key / string will only have it's properties instrumented. That is, if you want to instrument
      `window.fetch` function, you must specify `{"window": ["fetch",]}`. If you specify just `window.fetch` the
      instrumentation will try to instrument sub properties of `window.fetch` (which won't work as fetch is a
      function). As another example, to instrument window.document.cookie, you must use `{"window.document": ["cookie"]}`.
      In instances, such as `fetch`, where you do not need to specify `window.fetch`, but can use the alias `fetch`,
      in JavaScript code. The instrumentation `{"window": ["fetch",]}` will pick up calls to both `fetch()` and `window.fetch()`.

### `navigation_instrument`

TODO

### `callstack_instrument`

TODO

### `dns_instrument`

TODO

### `cookie_instrument`

- Data is saved to the `javascript_cookies` table.
- Will record cookies set both by JavaScript and via HTTP Responses

## Browser Profile Support

### Stateful vs Stateless crawls

By default OpenWPM performs a "stateful" crawl, in that it keeps a consistent
browser profile between page visits in the same browser. If the browser
freezes or crashes during the crawl, the profile is saved to disk and restored
before the next page visit.

It's also possible to run "stateless" crawls, in which each new page visit uses
a fresh browser profile. To perform a stateless crawl you can restart the
browser after each command sequence by setting the `reset` initialization
argument to `True` when creating the command sequence. As an example:

```python
manager = TaskManager.TaskManager(manager_params, browser_params)

for site in sites:
    command_sequence = CommandSequence.CommandSequence(site, reset=True)
    command_sequence.get(sleep=30, timeout=60)
    manager.execute_command_sequence(command_sequence)
```

In this example, the browser will `get` the requested `site`, sleep for 30
seconds, dump the profile cookies to the crawl database, and then restart the
browser before visiting the next `site` in `sites`.

### Loading and saving a browser profile

It's possible to load and save profiles during stateful crawls.

#### Save a profile

A browser's profile can be saved to disk for use in later crawls. This can be
done using a browser command or by setting a browser configuration parameter.
For long-running crawls we recommend saving the profile using the browser
configuration parameter as the platform will take steps to save the
profile in the event of a platform-level crash, whereas there is no guarantee
the browser command will run before a crash.

**Browser configuration parameter:** Set the `profile_archive_dir` browser
parameter to a directory where the browser profile should be saved. The profile
will be automatically saved when `TaskManager::close` is called or when a
platform-level crash occurs.

#### Load a profile

To load a profile, specify the `seed_tar` browser parameter in the browser
configuration dictionary. This should be a `Path` object pointing to the
`.tar` (or `.tar.gz` if compressed) file produced by OpenWPM
or by manually tarring a firefox profile directory.

> Please note that you must tar the contents of the profile directory
> and not the directory itself.  
> (For an example of the difference please see
> [here](https://github.com/openwpm/OpenWPM/issues/790#issuecomment-791316632))

The profile will be automatically extracted and loaded into the browser
instance for which the configuration parameter was set.

The profile specified by `seed_tar` will be loaded anytime the browser is
deliberately reset (i.e., using the `reset=True` CommandSequence argument),
but will not be used during crash recovery. Specifically:

- For stateful crawls the initial load of Firefox will use the
profile specified by `seed_tar`. If OpenWPM determines that Firefox needs to
restart for some reason during the crawl, it will use the profile from
the most recent page visit (pre-crash) rather than the `seed_tar` profile.
- For stateless crawls, the initial `seed_tar` will be loaded during each
new page visit. Note that this means the profile will very likely be
_incomplete_, as cookies or storage may have been set or changed during the
page load that are **not** reflected back into the seed profile.

## Non instrument data gathering

### Log Files

- Stored in the directory specified by `manager_params.data_directory`.
- Name specified by `manager_params.log_file`.

### Browser Profile

- Contains cookies, Flash objects, and so on that are dumped after a crawl
    is finished
- Automatically saved when the platform closes or crashes by specifying
    `browser_params.profile_archive_dir`.
- Save on-demand with the `CommandSequence::dump_profile` command.

### Rendered Page Source

- Save the top-level frame's rendered source with the
`CommandSequence::dump_page_source` command.
- Save the full rendered source (including all nested iframes) with the
`CommandSequence::recursive_dump_page_source` command.
  - The page source is saved in the following nested json structure:

        ```json
        {
            "doc_url": "http://example.com",
            "source": "<html> ... </html>",
            "iframes": {
                "frame_1": {"doc_url": "...",
                            "source": "...",
                            "iframes": { "...": "..." }},
                "frame_2": {"doc_url": "...",
                            "source": "...",
                            "iframes": { "...": "..." }},
                "frame_3": { "...": "..." }
            }
        }
        ```

### Screenshots

- Selenium 3 can be used to screenshot an individual element. None of the
    built-in commands offer this functionality, but you can use it when
    [writing your own](Using_OpenWPM.md#adding-a-new-command). See the [Selenium documentation](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html?highlight=element#selenium.webdriver.remote.webelement.WebElement.screenshot).
- Viewport screenshots (i.e. a screenshot of the portion of the website
    visible in the browser's window) are available with the
    `CommandSequence::save_screenshot` command.
- Full-page screenshots (i.e. a screenshot of the entire rendered DOM) are
    available with the `CommandSequence::screenshot_full_page` command.
  - This functionality is not yet supported by Selenium/geckodriver,
      though [it is planned](https://github.com/mozilla/geckodriver/issues/570).
      We produce screenshots by using JS to scroll the page and take a
      viewport screenshot at each location. This method will save the parts
      and a stitched version in the `screenshot_path`.
  - Since the screenshots are stitched they have some limitations:
    - On the area of the page present when the command is called will
          be captured. Sites which dynamically expand when scrolled (i.e.,
          infinite scroll) will only go as far as the original height.
    - We only scroll vertically, so pages that are wider than the
          viewport will be clipped.
    - In geckodriver v0.15 doing any scrolling (or having devtools
          open) seems to break element-only screenshots. So using this
          command will cause any future element-only screenshots to be
          misaligned.

### `save_content`

Response body content

- Saves all files encountered during the crawl to a `LevelDB`
    database de-duplicated by the md5 hash of the content.
- The `content_hash` column of the `http_responses` table contains the md5
    hash for each script, and can be used to do content lookups in the
    LevelDB content database.
- NOTE: this instrumentation may lead to performance issues when a large
    number of browsers are in use.
- Set `browser_params.save_content` to a comma-separated list of
    [resource_types](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType)
    to save only specific types of files, for instance
    `browser_params.save_content = "image,script"` to save Images and Javascript
    files. This will lessen the performance impact of this instrumentation
    when a large number of browsers are used in parallel. 
- You will also need to import LevelDbProvider from openwpm/storage/leveldb.py and instantiate it in the TaskManager in demo.py
