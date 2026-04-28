import { OpenWPMWebSocket } from "./websocket-client";

let crawlID = null;
let visitID = null;
let debugging = false;
let wsClient: OpenWPMWebSocket | null = null;

const commandCallback = async (msg) => {
  // Handle commands from Python (Initialize, Finalize, legacy visit_id)
  const action = msg.action;
  let newVisitID = msg.visit_id;
  switch (action) {
    case "Initialize":
      if (visitID) {
        logWarn("Set visit_id while another visit_id was set");
      }
      visitID = newVisitID;
      wsClient.sendRecord("meta_information", {
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
      wsClient.sendRecord("meta_information", {
        action: "Finalize",
        visit_id: newVisitID,
        browser_id: crawlID,
        success: true,
      });
      visitID = null;
      break;
    default:
      // Legacy: command contains just visit_id (no action field)
      if (newVisitID !== undefined) {
        newVisitID = parseInt(newVisitID, 10);
        logDebug("Setting visit_id the legacy way");
        visitID = newVisitID;
      } else {
        logWarn("Received unknown command: " + JSON.stringify(msg));
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

export const logInfo = function (msg) {
  // Always log to browser console
  console.log(msg);

  if (debugging) {
    return;
  }

  // Log level INFO == 20
  wsClient.sendLog(20, escapeString(msg));
};

export const logDebug = function (msg) {
  // Always log to browser console
  console.log(msg);

  if (debugging) {
    return;
  }

  // Log level DEBUG == 10
  wsClient.sendLog(10, escapeString(msg));
};

export const logWarn = function (msg) {
  // Always log to browser console
  console.warn(msg);

  if (debugging) {
    return;
  }

  // Log level WARN == 30
  wsClient.sendLog(30, escapeString(msg));
};

export const logError = function (msg) {
  // Always log to browser console
  console.error(msg);

  if (debugging) {
    return;
  }

  // Log level ERROR == 40
  wsClient.sendLog(40, escapeString(msg));
};

export const logCritical = function (msg) {
  // Always log to browser console
  console.error(msg);

  if (debugging) {
    return;
  }

  // Log level CRITICAL == 50
  wsClient.sendLog(50, escapeString(msg));
};

export const dataReceiver = {
  saveRecord(a, b) {
    console.log(a, b);
  },
};

export const saveRecord = function (instrument, record) {
  record.visit_id = visitID;

  if (!visitID && !debugging) {
    // Navigations to about:blank can be triggered by OpenWPM. We drop those.
    if (instrument === "navigations" && record.url === "about:blank") {
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
    record.visit_id = -1;
  }

  // send to console if debugging
  if (debugging) {
    console.log("EXTENSION", instrument, record);
    return;
  }
  wsClient.sendRecord(instrument, record);
};

// Stub for now
export const saveContent = async function (content, contentHash) {
  // Send page content to the data aggregator
  // deduplicated by contentHash in a levelDB database
  if (debugging) {
    console.log("LDB contentHash:", contentHash, "with length", content.length);
    return;
  }
  // Since the content might not be a valid utf8 string and it needs to be
  // json encoded later, it is encoded using base64 first.
  const b64 = Uint8ToBase64(content);
  wsClient.sendRecord("page_content", [b64, contentHash]);
};

// Base64 encoding, found on:
// https://stackoverflow.com/questions/12710001/how-to-convert-uint8-array-to-base64-encoded-string/25644409#25644409
function Uint8ToBase64(u8Arr) {
  const CHUNK_SIZE = 0x8000; // arbitrary number
  let index = 0;
  const length = u8Arr.length;
  let result = "";
  let slice;
  while (index < length) {
    slice = u8Arr.subarray(index, Math.min(index + CHUNK_SIZE, length));
    result += String.fromCharCode.apply(null, slice);
    index += CHUNK_SIZE;
  }
  return btoa(result);
}

export const escapeString = function (string) {
  // Convert to string if necessary
  if (typeof string !== "string") string = "" + string;
  return string;
};

export const boolToInt = function (bool) {
  return bool ? 1 : 0;
};
