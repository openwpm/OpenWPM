# Data gathering

There are a multitude of ways to collect data with OpenWPM some of them are listed here

Our general dataschema can be seen [here](Instrumentation-Schema-Documentation.md)


# Instruments

To activate a given instrument set `browser_params[i][instrument_name] = True`

## `http_instrument`
* HTTP Request and Response Headers, redirects, and POST request bodies
* Data is saved to the `http_requests`, `http_responses`, and `http_redirects`  tables.
    * `http_requests` schema
        [documentation](Instrumentation-Schema-Documentation.md#http-requests)
    * `channel_id` can be used to link a request saved in the
        `http_requests` table to its corresponding response in the
        `http_responses` table.
    * `channel_id` can also be used to link a request to the subsequent
        request that results after an HTTP redirect (3XX response). Use the
        `http_redirects` table, which includes a mapping between
        `old_channel_id`, the `channel_id` of the HTTP request that
        resulted in a 3XX response, and `new_channel_id`, the HTTP request
        that resulted from that redirect.
* OCSP POST request bodies are not recorded
* Note: request and response headers for cached content are also saved,
    with the exception of images.
    See: [Bug 634073](https://bugzilla.mozilla.org/show_bug.cgi?id=634073).
## `js_instrument`
* Records all method calls (with arguments) and property accesses for configured APIs
* Configure `browser_params['js_instrument_settings']` to desired settings.
* Data is saved to the `javascript` table.
* The full specification for `js_instrument_settings` is defined by a JSON schema.
  Details of that schema are available in [docs/schemas/README.md](../docs/schemas/README.md).
  In summary, a list is passed with JS objects to be instrumented and details about how
  that object should be instrumented. The js_instrument_settings you pass to browser_params
  will be validated python side against the JSON schema before the crawl starts running.
* A number of shortcuts are available to make writing `js_instrument_settings` less
  cumbersome than spelling out the full schema. These shortcuts are converted to a full
  specification by the `clean_js_instrumentation_settings` method in
  [automation/js_instrumentation.py](../automation/js_instrumentation.py).
* The first shortcut is the fingerprinting collection, specified by
  `collection_fingerprinting`. This was the default prior to v0.11.0. It contains a collection
  of APIs of potential fingerprinting interest:
    * HTML5 Canvas
    * HTML5 WebRTC
    * HTML5 Audio
    * Plugin access (via `navigator.plugins`)
    * MIMEType access (via `navigator.mimeTypes`)
    * `window.Storage`, `window.localStorage`, `window.sessionStorage`,
          and `window.name` access.
    * Navigator properties (e.g. `appCodeName`, `oscpu`, `userAgent`, ...)
    * Window properties (via `window.screen`)
* `collection_fingerprinting` is the default if `js_instrument` is `True`.
* The fingerprinting collection is specified by the json file
  [fingerprinting.json](../automation/js_instrumentation_collections/fingerprinting.json).
  This file is also a nice reference example for specifying your own APIs using the other
  shortcuts.
* Shortcuts:
    * Specifying just a string will instrument
      the whole API with the [default log settings](../docs/schemas/js_instrument_settings-settings-objects-properties-log-settings.md)
    * For just strings you can specify a [Web API](https://developer.mozilla.org/en-US/docs/Web/API)
      such as `XMLHttpRequest`. Or you can specify instances on window e.g. `window.document`.
    * Alternatively, you can specify a single-key dictionary that maps an API name to the properties / settings you'd
      like to use. The key of this dictionary can be an instance on `window` or a Web API.
      The value of this dictionary can be:
        * A list - this is a shortcut for `propertiesToInstrument` (see [log settings](../docs/schemas/js_instrument_settings-settings-objects-properties-log-settings.md))
        * A dictionary - with non default log settings. Items missing from this dictionary
          will be filled in with the default log settings.
    * Here are some examples:
        ```
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
    * Note, the key / string will only have it's properties instrumented. That is, if you want to instrument
      `window.fetch` function you must specify `{"window": ["fetch",]}`. If you specify just `window.fetch` the
      instrumentation will try to instrument sub properties of `window.fetch` (which won't work as fetch is a
      function). As another example, to instrument window.document.cookie, you must use `{"window.document": ["cookie"]}`.
      In instances, such as `fetch`, where you do not need to specify `window.fetch`, but can use the alias `fetch`,
      in JavaScript code. The instrumentation `{"window": ["fetch",]}` will pick up calls to both `fetch()` and `window.fetch()`.
## `save_content`
Response body content
* Saves all files encountered during the crawl to a `LevelDB`
    database de-duplicated by the md5 hash of the content.
* The `content_hash` column of the `http_responses` table contains the md5
    hash for each script, and can be used to do content lookups in the
    LevelDB content database.
* NOTE: this instrumentation may lead to performance issues when a large
    number of browsers are in use.
* Set `browser_params['save_content']` to a comma-separated list of
    [resource_types](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType)
    to save only specific types of files, for instance
    `browser_params['save_content'] = "script"` to save only Javascript
    files. This will lessen the performance impact of this instrumentation
    when a large number of browsers are used in parallel.
## `cookie_instrument`
* Data is saved to the `javascript_cookies` table.
* Will record cookies set both by Javascript and via HTTP Responses

# Non instrument data gathering
## Log Files
* Stored in the directory specified by `manager_params['data_directory']`.
* Name specified by `manager_params['log_file']`.
## Browser Profile
* Contains cookies, Flash objects, and so on that are dumped after a crawl
    is finished
* Automatically saved when the platform closes or crashes by specifying
    `browser_params['profile_archive_dir']`.
* Save on-demand with the `CommandSequence::dump_profile` command.
## Rendered Page Source
* Save the top-level frame's rendered source with the
`CommandSequence::dump_page_source` command.
* Save the full rendered source (including all nested iframes) with the
`CommandSequence::recursive_dump_page_source` command.
    * The page source is saved in the following nested json structure:
        ```
        {
            'doc_url': "http://example.com",
            'source': "<html> ... </html>",
            'iframes': {
                'frame_1': {'doc_url': ...,
                            'source': ...,
                            'iframes: { ... }},
                'frame_2': {'doc_url': ...,
                            'source': ...,
                            'iframes: { ... }},
                'frame_3': { ... }
            }
        }
        ```
## Screenshots
* Selenium 3 can be used to screenshot an individual element. None of the
    built-in commands offer this functionality, but you can use it when
    [writing your own](Using_OpenWPM.md#adding-a-new-command). See the [Selenium documentation](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html?highlight=element#selenium.webdriver.remote.webelement.WebElement.screenshot).
* Viewport screenshots (i.e. a screenshot of the portion of the website
    visible in the browser's window) are available with the
    `CommandSequence::save_screenshot` command.
* Full-page screenshots (i.e. a screenshot of the entire rendered DOM) are
    available with the `CommandSequence::screenshot_full_page` command.
    * This functionality is not yet supported by Selenium/geckodriver,
      though [it is planned](https://github.com/mozilla/geckodriver/issues/570).
      We produce screenshots by using JS to scroll the page and take a
      viewport screenshot at each location. This method will save the parts
      and a stitched version in the `screenshot_path`.
    * Since the screenshots are stitched they have some limitations:
        * On the area of the page present when the command is called will
          be captured. Sites which dynamically expand when scrolled (i.e.,
          infinite scroll) will only go as far as the original height.
        * We only scroll vertically, so pages that are wider than the
          viewport will be clipped.
        * In geckodriver v0.15 doing any scrolling (or having devtools
          open) seems to break element-only screenshots. So using this
          command will cause any future element-only screenshots to be
          misaligned.
