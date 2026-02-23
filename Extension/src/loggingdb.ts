import { escapeString, Uint8ToBase64 } from "./lib/string-utils";
import { OpenWPMWebSocket } from "./websocket-client";

/**
 * Control message from Python: either an Initialize/Finalize action or a bare
 * legacy visit id (number or numeric string), which is why the callback also
 * handles non-object payloads.
 */
interface VisitControlMessage {
  action?: "Initialize" | "Finalize";
  visit_id?: number;
  browser_id?: number | null;
  success?: boolean;
}

let crawlID: number | null = null;
let visitID: number | null = null;
let debugging = false;
let wsClient: OpenWPMWebSocket | null = null;

const commandCallback = async (data: unknown) => {
  // Handle commands from Python (Initialize, Finalize, legacy visit_id).
  // This works even if data is a bare visit id.
  const message = data as VisitControlMessage;
  const action = message.action;
  let newVisitID = message.visit_id ?? null;
  switch (action) {
    case "Initialize":
      if (visitID) {
        logWarn("Set visit_id while another visit_id was set");
      }
      visitID = newVisitID;
      wsClient?.sendRecord("meta_information", {
        action: "Initialize",
        visit_id: newVisitID,
        browser_id: crawlID,
      });
      break;
    case "Finalize":
      if (!visitID) {
        logWarn("Received Finalize while no visit_id was set");
      }
      if (newVisitID !== visitID) {
        logError(
          "Received Finalize but visit_id didn't match. " +
            `Current visit_id ${newVisitID}, received visit_id ${visitID}.`,
        );
      }
      wsClient?.sendRecord("meta_information", {
        action: "Finalize",
        visit_id: newVisitID,
        browser_id: crawlID,
        success: true,
      });
      visitID = null;
      break;
    default:
      // Legacy: command is a bare visit id with no action field.
      if (newVisitID !== null) {
        newVisitID = parseInt(String(newVisitID), 10);
        logDebug("Setting visit_id the legacy way");
        visitID = newVisitID;
      } else {
        logWarn("Received unknown command: " + JSON.stringify(data));
      }
  }
};

export const open = async function (
  websocketPort: number,
  curr_crawlID: number,
) {
  if (websocketPort == null && curr_crawlID === 0) {
    console.log("Debugging, everything will output to console");
    debugging = true;
    return;
  }
  crawlID = curr_crawlID;

  console.log("Opening WebSocket connection...");

  wsClient = new OpenWPMWebSocket(commandCallback);
  await wsClient.connect(websocketPort);
  console.log("WebSocket connected to port", websocketPort);
};

export const close = function () {
  if (wsClient != null) {
    wsClient.close();
  }
};

export const logInfo = function (msg: string) {
  // Always log to browser console
  console.log(msg);

  if (debugging) {
    return;
  }

  // Log level INFO == 20
  wsClient?.sendLog(20, escapeString(msg));
};

export const logDebug = function (msg: string) {
  // Always log to browser console
  console.log(msg);

  if (debugging) {
    return;
  }

  // Log level DEBUG == 10
  wsClient?.sendLog(10, escapeString(msg));
};

export const logWarn = function (msg: string) {
  // Always log to browser console
  console.warn(msg);

  if (debugging) {
    return;
  }

  // Log level WARN == 30
  wsClient?.sendLog(30, escapeString(msg));
};

export const logError = function (msg: string) {
  // Always log to browser console
  console.error(msg);

  if (debugging) {
    return;
  }

  // Log level ERROR == 40
  wsClient?.sendLog(40, escapeString(msg));
};

export const logCritical = function (msg: string) {
  // Always log to browser console
  console.error(msg);

  if (debugging) {
    return;
  }

  // Log level CRITICAL == 50
  wsClient?.sendLog(50, escapeString(msg));
};

/**
 * The bookkeeping fields this module reads or stamps onto every record before
 * persisting it. Instruments build concrete, fully typed records (e.g.
 * `JavascriptCookieRecord`); we view them through this narrow shape.
 */
interface InstrumentRecordFields {
  visit_id?: number | null;
  url?: string;
}

export const dataReceiver = {
  saveRecord(instrument: string, record: object) {
    console.log(instrument, record);
  },
};

export const saveRecord = function (instrument: string, record: object) {
  const fields = record as InstrumentRecordFields;
  fields.visit_id = visitID;

  if (!visitID && !debugging) {
    // Navigations to about:blank can be triggered by OpenWPM. We drop those.
    if (instrument === "navigations" && fields.url === "about:blank") {
      logDebug(
        "Extension-" +
          crawlID +
          " : Dropping navigation to about:blank in intermediate period",
      );
      return;
    }
    logWarn(
      `Extension-${crawlID} : visitID is null while attempting to insert into table ${instrument}\n` +
        JSON.stringify(record),
    );
    fields.visit_id = -1;
  }

  // send to console if debugging
  if (debugging) {
    console.log("EXTENSION", instrument, record);
    return;
  }
  wsClient?.sendRecord(instrument, record);
};

// Stub for now
export const saveContent = async function (
  content: string | Uint8Array,
  contentHash: string,
) {
  // Send page content to the data aggregator
  // deduplicated by contentHash in a levelDB database
  if (debugging) {
    console.log("LDB contentHash:", contentHash, "with length", content.length);
    return;
  }
  // Since the content might not be a valid utf8 string and it needs to be
  // json encoded later, it is encoded using base64 first.
  const bytes =
    typeof content === "string" ? new TextEncoder().encode(content) : content;
  const b64 = Uint8ToBase64(bytes);
  wsClient?.sendRecord("page_content", [b64, contentHash]);
};
