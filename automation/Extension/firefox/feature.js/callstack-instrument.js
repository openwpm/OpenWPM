/*
    This script catches the stacktraces of JavaScript that ran on a crawled site and made a WebRequest
    and saves them to the "callstacks" table
*/
export class CallstackInstrument {
    constructor(dataReceiver) {
        this.dataReceiver = dataReceiver;
    }
    run(crawlID) {
        browser.stackDump.onStackAvailable.addListener((requestId, stack) => {
            const record = {
                crawl_id: crawlID,
                request_id: requestId,
                call_stack: stack
            };
            this.dataReceiver.saveRecord("callstacks", record);
        });
    }
}