/*
  We capture the JS callstack when we detect a dynamically created http request
  and bubble it up via a WebExtension Experiment API stackDump.
  This instrumentation captures those and saves them to the "callstacks" table.
*/
export class CallstackInstrument {
  dataReceiver: any;
  constructor(dataReceiver: typeof import("./loggingdb")) {
    this.dataReceiver = dataReceiver;
  }
  run(browser_id: number) {
    (browser as any).stackDump.onStackAvailable.addListener(
      (request_id, call_stack) => {
        const record = {
          browser_id,
          request_id,
          call_stack,
        };
        this.dataReceiver.saveRecord("callstacks", record);
      },
    );
  }
}
