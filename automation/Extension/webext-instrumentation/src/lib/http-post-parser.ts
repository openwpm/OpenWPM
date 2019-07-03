// Incorporates code from: https://github.com/redline13/selenium-jmeter/blob/6966d4b326cd78261e31e6e317076569051cac37/content/library/recorder/HttpPostParser.js

import {
  WebRequestOnBeforeRequestEventDetails,
  // WebRequestOnBeforeSendHeadersEventDetails,
} from "../types/browser-web-request-event-details";
// import { escapeString, escapeUrl } from "./string-utils";

import { Uint8ToBase64 } from "./string-utils";

// const components: any = {};

export interface ParsedPostRequest {
  post_headers?: any;
  post_body?: any;
  post_body_raw?: string;
}

export class HttpPostParser {
  // private readonly onBeforeSendHeadersEventDetails: WebRequestOnBeforeSendHeadersEventDetails;
  private readonly onBeforeRequestEventDetails: WebRequestOnBeforeRequestEventDetails;
  private readonly dataReceiver;
  /*
  private hasheaders: boolean;
  private seekablestream;
  private stream;
  private postBody;
  private postLines;
  private postHeaders;
  private body;
  */

  constructor(
    // onBeforeSendHeadersEventDetails: WebRequestOnBeforeSendHeadersEventDetails,
    onBeforeRequestEventDetails: WebRequestOnBeforeRequestEventDetails,
    dataReceiver,
  ) {
    // this.onBeforeSendHeadersEventDetails = onBeforeSendHeadersEventDetails;
    this.onBeforeRequestEventDetails = onBeforeRequestEventDetails;
    this.dataReceiver = dataReceiver;
    /*
    console.log(
      "HttpPostParser",
      // onBeforeSendHeadersEventDetails,
      onBeforeRequestEventDetails,
    );
    */
  }

  /**
   * @param encodingType from the HTTP Request headers
   */
  public parsePostRequest(/*encodingType*/) {
    // const requestHeaders = this.onBeforeSendHeadersEventDetails.requestHeaders;
    const requestBody = this.onBeforeRequestEventDetails.requestBody;
    if (requestBody.error) {
      this.dataReceiver.logError(
        "Exception: Upstream failed to parse POST: " + requestBody.error,
      );
    }
    if (requestBody.formData) {
      return {
        // TODO: requestBody.formData should probably be transformed into another format
        post_body: requestBody.formData,
      };
    }
    if (requestBody.raw) {
      return {
        post_body_raw: JSON.stringify(
          requestBody.raw.map(x => [
            x.file,
            Uint8ToBase64(new Uint8Array(x.bytes)),
          ]),
        ),
      };
    }

    // Return empty response until we have all instrumentation converted
    return {};
    /*
    this.dataReceiver.logDebug(
      "Exception: Instrumentation to parse POST requests without formData is not yet restored",
    );

    // TODO: Refactor to corresponding webext logic or discard
    try {
      this.setupStream();
      this.parseStream();
    } catch (e) {
      this.dataReceiver.logError("Exception: Failed to parse POST: " + e);
      return {};
    }

    const postBody = this.postBody;

    if (!postBody) {
      // some scripts strangely sends empty post bodies (confirmed with the developer tools)
      return {};
    }

    let isMultiPart = false; // encType: multipart/form-data
    const postHeaders = this.postHeaders; // request headers from upload stream
    // See, http://stackoverflow.com/questions/16548517/what-is-request-headers-from-upload-stream

    // add encodingType from postHeaders if it's missing
    if (!encodingType && postHeaders && "Content-Type" in postHeaders) {
      encodingType = postHeaders["Content-Type"];
    }

    if (encodingType.indexOf("multipart/form-data") !== -1) {
      isMultiPart = true;
    }

    let jsonPostData = "";
    let escapedJsonPostData = "";
    if (isMultiPart) {
      jsonPostData = this.parseMultiPartData(postBody /*, encodingType* /);
      escapedJsonPostData = escapeString(jsonPostData);
    } else {
      jsonPostData = this.parseEncodedFormData(postBody, encodingType);
      escapedJsonPostData = escapeString(jsonPostData);
    }
    return { post_headers: postHeaders, post_body: escapedJsonPostData };
    */
  }
  /*
  private setupStream() {
    // TODO: Refactor to corresponding webext logic or discard (it may be relevant
    // to parse the this.onBeforeRequestEventDetails.requestBody.raw.bytes property)
    const stream = null;
    // Scriptable Stream Constants
    this.seekablestream = stream;
    this.stream = components.classes[
      "@mozilla.org/scriptableinputstream;1"
    ].createInstance(components.interfaces.nsIScriptableInputStream);
    this.stream.init(this.seekablestream);

    this.postBody = "";
    this.postLines = [];
    this.postHeaders = [];
    // Check if the upload stream has headers based on the stream type
    // By "headers" we mean "Request Headers From Upload Stream", which are sent in the
    // POST request body and separate from the standard HTTP headers:
    // http://stackoverflow.com/questions/16548517/what-is-request-headers-from-upload-stream

    // If this an unknown stream, we assume it doesn't contain headers
    // We verified the list of streams that contain headers using various encoding types
    // and payload formats tested in the TestPOSTInstrument class
    // Also see, https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XPCOM/Guide/Streams
    this.hasheaders = false;
    this.body = 0;
    if (
      this.seekablestream instanceof components.interfaces.nsIMIMEInputStream
    ) {
      // form submissions use nsIMIMEInputStream
      this.seekablestream.QueryInterface(
        components.interfaces.nsIMIMEInputStream,
      );
      this.hasheaders = true;
      this.body = -1;
    } else if (
      this.seekablestream instanceof components.interfaces.nsIStringInputStream
    ) {
      // AJAX requests use nsIStringInputStream, except when the payload is "FormData"
      this.seekablestream.QueryInterface(
        components.interfaces.nsIStringInputStream,
      );
      this.hasheaders = true;
      this.body = -1;
    } else if (
      0 &&
      this.seekablestream instanceof
        components.interfaces.nsIMultiplexInputStream
    ) {
      // AJAX requests with "FormData" payload use nsIMultiplexInputStream
      this.seekablestream.QueryInterface(
        components.interfaces.nsIMultiplexInputStream,
      );
      this.hasheaders = true;
      this.body = -1;
    } else {
      // Let's keep an eye on unknown stream types, though we haven't seen any other stream types in our tests.
      this.dataReceiver.logDebug("POST request parser: unknown stream type");
    }
  }

  private rewind() {
    this.seekablestream.seek(0, 0);
  }

  private tell() {
    return this.seekablestream.tell();
  }

  private readLine() {
    let line = "";
    const size = this.stream.available();
    for (let i = 0; i < size; i++) {
      const c = this.stream.read(1);
      if (c === "\r") {
        continue;
      } else if (c === "\n") {
        break;
      } else {
        line += c;
      }
    }
    return line;
  }

  private extractUploadStreamHeaders() {
    /*
     * Extract "Request Headers From Upload Stream" from the POST request body.
     * Unlike standard HTTP headers, these headers are sent in the request body
     * and contain metadata such as the size and the encoding of the submitted data
     * (e.g. multi-part form data)
     * Also, seee http://stackoverflow.com/questions/16548517/what-is-request-headers-from-upload-stream
     * A sample POST request body with upload stream headers (from the `test_record_post_data_multipart_formdata`)
     *
      Content-Type: multipart/form-data; boundary=---------------------------1809321333852408290275809649
      Content-Length: 455

      -----------------------------1809321333852408290275809649
      Content-Disposition: form-data; name="email"
      [snipped]
     * /
    if (this.hasheaders) {
      this.rewind();
      let line = this.readLine();
      while (line) {
        const keyValue = line.match(/^([^:]+):\s?(.*)/);
        if (keyValue) {
          this.postHeaders[keyValue[1]] = keyValue[2];
        } else {
          this.postLines.push(line);
        }
        line = this.readLine();
      }
      this.body = this.tell();
    }
  }

  private convertTextPlainToUrlEncoded(postBody) {
    /* Convert from text/plain to application/x-www-form-urlencoded
     * This is to unify the encoding so that we can parse different encodings at one place
      See, https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest#Using_nothing_but_XMLHttpRequest

      We convert from (text/plain )...
        foo=bar
        baz=The first line.
        The second line.
      to (application/x-www-form-urlencoded):
        foo=bar&baz=The+first+line.%0D%0AThe+second+line.%0D%0A
     * /
    const lines = postBody.split("\n");
    const post_vars = [];
    for (const line of lines) {
      if (line.indexOf("=") !== -1) {
        post_vars.push(encodeURIComponent(line.trim()));
      } else {
        const x = encodeURIComponent("\r\n" + line.trim());
        post_vars.push(post_vars.pop() + x);
      }
    }
    return post_vars.join("&");
  }

  private parseEncodedFormData(formData, encodingType) {
    const obj = {};

    if (formData.indexOf("=") === -1) {
      // not key=value form
      return formData;
    }

    const origFormData = formData; // keep the original form data

    try {
      if (encodingType.indexOf("text/plain") !== -1) {
        formData = this.convertTextPlainToUrlEncoded(formData);
      }

      // URL encoded formData in key=value form should only have one equal sign,
      // other equal signs should have been encoded away at this point.
      // If we've ==, this means this is unstructured data (e.g. base64 string),
      // and we won't be able to parse it into key-value pairs.
      if (formData.indexOf("==") !== -1) {
        return origFormData;
      }

      formData = decodeURIComponent(formData.replace(/\+/g, " "));
      // read key=value pairs, based on http://stackoverflow.com/a/8648962
      // If we have non key-value data that contains "=", we treat it as
      // key=value data (unless if it contains two equal signs, see above)
      // This may have the side effect of over-parsing some POST data
      // although the effect should be reversible.
      // The catch is, one can create ambiguous POST data, where it may be
      // impossible to tell the real format (key=value or not).
      // TODO: we could consider alternatives such as storing the original POST
      // data for debugging or not parsing the POST body in the extension at all.
      formData.replace(/([^=&]+)=([^&]*)/g, function(_m, key, value) {
        obj[key] = value;
      });
      return JSON.stringify(obj);
    } catch (e) {
      // We expect to have parsing failures due to unstructured POST data
      // e.g. In test_record_binary_post_data, decodeURIComponent throws a URIError
      // for binary data posted via AJAX.
      this.dataReceiver.logDebug(
        "POST data is not parseable:" +
          e +
          " EncodingType:" +
          encodingType +
          " PostDataLength:" +
          origFormData.length +
          " PostDataType:" +
          typeof origFormData +
          " PostData:" +
          escapeString(origFormData) +
          "\n",
      );
      return origFormData; // return the original body
    }
  }

  private parseMultiPartData(formData /*, encodingType* /) {
    /*
     * Parse POST bodies with encType "multipart/form-data encoded"
     * https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types#multipartform-data
     *
     * formData is in the following form:
     *
      -----------------------------12972102761018453617355621459
      Content-Disposition: form-data; name="email"

      test@example.com
      -----------------------------12972102761018453617355621459
      Content-Disposition: form-data; name="username"

      name surname+
      -----------------------------12972102761018453617355621459--
      * /
    let boundary = "";
    const firstLine = formData.split("\r\n", 1)[0];
    if (firstLine.startsWith("-----------------------------")) {
      boundary = firstLine;
    } else {
      return formData;
    } // return unparsed data, if we fail to find the boundary string

    const formVars = {};
    for (const part of formData.split(boundary)) {
      const partData = this.parseSinglePart(part);
      if ("key" in partData && "value" in partData) {
        formVars[partData.key] = partData.value;
      }
    }
    return JSON.stringify(formVars);
  }

  private notContentHeader(partLine) {
    // Filter function to discard content headers present in the multipart form data
    // See, http://stackoverflow.com/a/16548608
    return !partLine.match(/^Content-.*: .* /);
  }

  private parseSinglePart(part) {
    /*
     * Parse a single part of a multipart request body
     *
     * A part of multipart form data is as follows:
     *
       Content-Disposition: form-data; name="username"

       name surname+
    * /
    part = part.trim();
    if (!part || part === "--") {
      // ignore empty parts or extra characters after the last boundary
      return {};
    }

    const partLines = part.split("\r\n");

    const matchVarName = partLines[0].match(
      /Content-Disposition:.*;.name="([^"]*)"/,
    );
    if (matchVarName) {
      return {
        key: matchVarName[1],
        value: partLines
          .slice(1)
          .filter(this.notContentHeader)
          .join("\r\n")
          .trim(),
      };
    } else {
      this.dataReceiver.logError(
        "Can't find the POST variable name in " + part,
      );
      return {};
    }
  }

  private parseStream() {
    // Position the stream to the start of the body
    if (this.body < 0 || this.seekablestream.tell() !== this.body) {
      this.extractUploadStreamHeaders();
    }

    let size = this.stream.available();
    if (size === 0 && this.body !== 0) {
      // whoops, there weren't really headers..
      this.rewind();
      this.hasheaders = false;
      size = this.stream.available();
    }
    let postString = "";
    try {
      // This is to avoid 'NS_BASE_STREAM_CLOSED' exception that may occurs
      // See bug #188328.
      for (let i = 0; i < size; i++) {
        const c = this.stream.read(1);
        c ? (postString += c) : (postString += "\0");
      }
    } catch (ex) {
      this.dataReceiver.logError("Error parsing the POST request: " + ex);
      return;
    } finally {
      this.rewind();
    }

    // strip off trailing \r\n's
    while (postString.indexOf("\r\n") === postString.length - 2) {
      postString = postString.substring(0, postString.length - 2);
    }
    this.postBody = postString.trim();
  }
  */
}
