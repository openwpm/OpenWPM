/*
  We capture the JS callstack when we detect a dynamically created http request
  and bubble it up via a WebExtension Experiment API stackDump.
  This instrumentation captures those and saves them to the "callstacks" table.
*/
export class CallstackInstrument {
  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }
  run(crawl_id) {
    browser.stackDump.onStackAvailable.addListener((request_id, call_stack) => {
      const record = {
        crawl_id,
        request_id,
        call_stack
      };
      this.dataReceiver.saveRecord("callstacks", record);
    });
  }
}