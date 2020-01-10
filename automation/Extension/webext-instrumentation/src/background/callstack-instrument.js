
export class CallstackInstrument {
    constructor(dataReceiver) {
        this.dataReceiver = dataReceiver;
    }
    async run(crawlID) {
        browser.stackDump.onStackAvailable.addListener((requestId, stack) => {
            const record = {
                crawl_id: crawlID,
                request_id: requestId,
                call_stack: stack
            }
            console.log("Extension Callstack does this even run?")
            await this.dataReceiver.saveRecord("callstacks", record)
        });
    }
}