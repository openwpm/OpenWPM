import { escapeString, Uint8ToBase64 } from "openwpm-webext-instrumentation";


// Make the function wait until the connection is made...
function waitForSocketConnection(socket, callback) {
    setTimeout(
        function () {
            if (socket.readyState === socket.OPEN) {
                callback();
            } else {
                console.log("Waiting for websocket...")
                waitForSocketConnection(socket, callback);
            }
        }, 5); // wait 5 milisecond for the connection...
};


export class Logger {

    constructor(wsAddress, crawlID, visitID, testing=false) {
        if (testing === true) {
            console.log("Debugging, everything will output to console");
            this.debugging = true;
            return;
        } else {
            this.debugging = false;
        }

        this.crawlID = crawlID;
        this.visitID = visitID;

        let wsPath = 'ws://' + wsAddress[0] + ':' + wsAddress[1];
        console.log('WebSocket Path is: ', wsPath);
        this.socket = new WebSocket(wsPath);
        this.send("VisitID: " + visitID + " || CrawlID: " + crawlID);
    }

    send(msg) {
        waitForSocketConnection(this.socket, () => {
            this.socket.send(msg);
        })
    }

    close() {
        waitForSocketConnection(this.socket, () => {
            this.socket.close();
        })
    }

    makeLogJSON(level, msg) {
        var log_json = {
            'name': 'Extension-Logger',
            'level': level,
            'pathname': 'FirefoxExtension',
            'lineno': 1,
            'msg': escapeString(msg),
            'args': null,
            'exc_info': null,
            'func': null
        }
        return log_json;
    }

    logInfo(msg) {
        // Always log to browser console
        console.log(msg);

        if (this.debugging) {
            return;
        }

        // Log level INFO == 20 (https://docs.python.org/2/library/logging.html#logging-levels)
        var log_json = this.makeLogJSON(20, msg);
        this.send(['LOG EXTENSION', JSON.stringify(log_json)]);
    }

    logDebug(msg) {
        // Always log to browser console
        console.log(msg);

        if (this.debugging) {
            return;
        }

        // Log level DEBUG == 10 (https://docs.python.org/2/library/logging.html#logging-levels)
        var log_json = this.makeLogJSON(10, msg);
        this.send(['LOG EXTENSION', JSON.stringify(log_json)]);
    }

    logWarn(msg) {
        // Always log to browser console
        console.warn(msg);

        if (this.debugging) {
            return;
        }

        // Log level WARN == 30 (https://docs.python.org/2/library/logging.html#logging-levels)
        var log_json = this.makeLogJSON(30, msg);
        this.send(['LOG EXTENSION', JSON.stringify(log_json)]);
    }

    logError(msg) {
        // Always log to browser console
        console.error(msg);

        if (this.debugging) {
            return;
        }

        // Log level INFO == 40 (https://docs.python.org/2/library/logging.html#logging-levels)
        var log_json = this.makeLogJSON(40, msg);
        this.send(['LOG EXTENSION', JSON.stringify(log_json)]);
    }

    logCritical(msg) {
        // Always log to browser console
        console.error(msg);

        if (this.debugging) {
            return;
        }

        // Log level CRITICAL == 50 (https://docs.python.org/2/library/logging.html#logging-levels)
        var log_json = this.makeLogJSON(50, msg);
        this.send(['LOG EXTENSION', JSON.stringify(log_json)]);
    }

    saveRecord(instrument_type, record) {
        if (!this.visitID && !this.debugging) {
            this.logCritical(
                'Extension-' + this.crawlID + 
                ' : visitID is null while attempting to insert ' + JSON.stringify(record)
            );
        }
        if (this.debugging) {
            console.log("EXTENSION", instrument_type, JSON.stringify(record));
            return;
        }
        record["visit_id"] = this.visitID;
        this.send(["DATA " + instrument_type, JSON.stringify(record)]); 
    }

    saveContent(content, contentHash) {
        // Send page content to the data aggregator
        // deduplicated by contentHash in a levelDB database
        if (this.debugging) {
            console.log("Content Hash: ", contentHash, " with length", content.length);
            return;
        }
        // Since the content might not be a valid utf8 string and it needs to be
        // json encoded later, it is encoded using base64 first.
        let b64 = Uint8ToBase64(content);
        this.send(["DATA " + page_content, [b64, contentHash]]);
    }

}