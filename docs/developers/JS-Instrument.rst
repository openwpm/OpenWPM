JS Instrument technical documentation
=====================================

Of all the Instruments in the OpenWPM webextension the one that is most likely
to collect the most information is the Javascript instrument.
It allows users to specify which WebAPI calls they are interested in and 
receive a full breadth of information on how websites use the instrumented APIs.

To allow for this rich data collection it employs a number of tricks and subtelties
which this document aims to capture.

Setting up the instrumentation
------------------------------

TL;DR: We pass the configuration to a content script in the webextension. In the content
scope generate a string that contains the script we want to execute on the page
and then insert it in into the page.
This script is literally a format string in which the configuration gets embedded via
`JSON.stringify`.

Data collection
---------------

TL;DR: We wrap each WebAPI that we should instrument and forward all calls to us
to the underlying object, while logging the accesses. This is done by the injected
script mentioned above.

Getting the data into the Database
----------------------------------

Since the data collection happens in the website scope, but we care about it
in the in the database, we had to figure out a way to get it there.

We do this via the following steps:

1. Dispatch a custom event via `document.dispatchEvent` in `javascript-instrumentat-page-scope`
2. Register a listener for the custom event in `javascript-instrument-content-scope` and
   call `runtime.sendMessage` to pass it from the content scope into the background scope
3. Where `js-instrument` receives the message and forwards it to the `loggingdb`