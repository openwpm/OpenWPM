// Incorporates code from: https://github.com/redline13/selenium-jmeter/blob/6966d4b326cd78261e31e6e317076569051cac37/content/library/recorder/HttpPostParser.js

const {Cc, Ci, CC, Cu, components} = require("chrome");
var loggingDB     = require("./loggingdb.js");

var HttpPostParser = function(stream) {
  // Scriptable Stream Constants
  this.seekablestream = stream;
  this.stream = components.classes["@mozilla.org/scriptableinputstream;1"].createInstance(components.interfaces.nsIScriptableInputStream);
  this.stream.init(this.seekablestream);

  this.postBody = "";
  this.postLines = [];
  this.postHeaders = [];
  // Check if the stream has headers
  this.hasheaders = false;
  this.body = 0;
  if (this.seekablestream instanceof components.interfaces.nsIMIMEInputStream) {
    this.seekablestream.QueryInterface(components.interfaces.nsIMIMEInputStream);
    this.hasheaders = true;
    this.body = -1;
  } else if (this.seekablestream instanceof components.interfaces.nsIStringInputStream) {
    this.seekablestream.QueryInterface(components.interfaces.nsIStringInputStream);
    this.hasheaders = true;
    this.body = -1;
  }
}

HttpPostParser.prototype.rewind = function() {
  this.seekablestream.seek(0, 0);
};

HttpPostParser.prototype.tell = function() {
  return this.seekablestream.tell();
};

HttpPostParser.prototype.readLine = function() {
  var line = "";
  var size = this.stream.available();
  for (var i = 0; i < size; i++) {
    var c = this.stream.read(1);
    if (c == '\r') {
    } else if (c == '\n') {
      break;
    } else {
      line += c;
    }
  }
  return line;
};

// visitor can be null, function has side-effect of setting body
HttpPostParser.prototype.headers = function() {
  if (this.hasheaders) {
    this.rewind();
    var line = this.readLine();
    while (line) {
      var keyValue = line.match(/^([^:]+):\s?(.*)/);
      // match can return null...
      if (keyValue) {
        this.postHeaders[keyValue[1]] = keyValue[2];
      } else {
        this.postLines.push(line);
      }
      line = this.readLine();
    }
    this.body = this.tell();
  }
};

HttpPostParser.prototype.convertTextPlainToUrlEncoded = function(postBody){
  /* Convert from text/plain to application/x-www-form-urlencoded
   * This is to unify the encoding so that we can parse different encodings at one place
    See, https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest#Using_nothing_but_XMLHttpRequest

    We convert from (text/plain )...
      foo=bar
      baz=The first line.
      The second line.
    to (application/x-www-form-urlencoded):
      foo=bar&baz=The+first+line.%0D%0AThe+second+line.%0D%0A
   */
  var lines = postBody.split("\n");
  var post_vars = [];
  for (var line of lines){
    if (line.indexOf("=") != -1) {
      post_vars.push(encodeURIComponent(line.trim()));
    } else {
      var x = encodeURIComponent("\r\n" + line.trim());
      post_vars.push(post_vars.pop() + x);
    }
  }
  return post_vars.join("&");
}

HttpPostParser.prototype.parseEncodedFormData = function(formData, encodingType){
  var obj = {};

  if (formData.indexOf("=") == -1)  // not key=value form
    return formData;

  try{
    if (encodingType.indexOf("text/plain") != -1)
      formData = this.convertTextPlainToUrlEncoded(formData);

    formData = decodeURIComponent(formData.replace(/\+/g,  " "));
    // read key=value pairs, based on http://stackoverflow.com/a/8648962
    formData.replace(/([^=&]+)=([^&]*)/g, function(m, key, value) {
      obj[key] = value;
    });
    return JSON.stringify(obj);
  }catch (e) {
    console.log("Exception: Cannot parse POST data:", e, encodingType, "formData:", formData);
    return formData;  // return the original body if we can't decode
  }
}


HttpPostParser.prototype.parsePostRequest = function(encodingType){
  try {
    this.parseStream();
  } catch (e) {
    console.log( "Exception: Failed to parse POST", e );
    return {};
  }

  var postBody = this.postBody;

  if (!postBody)  // some scripts strangely sends empty post bodies (confirmed with the developer tools)
    return {};

  var isMultiPart = false;  // encType: multipart/form-data
  var postHeaders = this.postHeaders;  // request headers from upload stream
  // See, http://stackoverflow.com/questions/16548517/what-is-request-headers-from-upload-stream

  // add encodingType from postHeaders if it's missing
  if (!encodingType && postHeaders && ("Content-Type" in postHeaders))
    encodingType = postHeaders["Content-Type"];

  if (encodingType.indexOf("multipart/form-data") != -1)
    isMultiPart = true;

  var jsonPostData = "";
  var escapedJsonPostData = "";
  if (isMultiPart) {
    jsonPostData = this.parseMultiPartData(postBody, encodingType);
    escapedJsonPostData = loggingDB.escapeString(jsonPostData);
  } else {
    jsonPostData = this.parseEncodedFormData(postBody, encodingType);
    escapedJsonPostData = loggingDB.escapeString(jsonPostData);
  }
  return {post_headers: postHeaders, post_body: escapedJsonPostData};
};



HttpPostParser.prototype.parseMultiPartData = function(formData, encodingType) {
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
    */
  var boundary = "";
  var firstLine = formData.split("\r\n", 1)[0];
  if (firstLine.startsWith("-----------------------------"))
    boundary = firstLine;
  else
    return formData;  // return unparsed data, if we fail to find the boundary string

  var formVars = {};
  for (var part of formData.split(boundary)){
    partData = this.parseSinglePart(part);
    if ("key" in partData && "value" in partData)
      formVars[partData["key"]] = partData["value"];
  }
  return JSON.stringify(formVars);
}


HttpPostParser.prototype.parseSinglePart = function(part) {
  /*
   * Parse a single part of a multipart request body
   * e.g., one part is as follows:
     Content-Disposition: form-data; name="username"

     name surname+
  */
  part = part.trim();
  if (!part || part === "--")  // ignore empty parts or extra characters after the last boundary
    return {};

  var partLines = part.split("\r\n");

  var matchVarName = partLines[0].match(/Content-Disposition:.*;.name="([^"]*)"/);
  if (matchVarName) {
    return {key: matchVarName[1],
            value: partLines.slice(1).join("\r\n").trim()};
  } else {
    console.log("Can't find the POST form data variable name in", part);
    return {};
  }
}

HttpPostParser.prototype.parseStream = function() {
  // Position the stream to the start of the body
  if (this.body < 0 || this.seekablestream.tell() != this.body) {
    this.headers();
  }

  var size = this.stream.available();
  if (size == 0 && this.body != 0) {
    // whoops, there weren't really headers..
    this.rewind();
    this.hasheaders = false;
    size = this.stream.available();
  }
  var postString = "";
  try {
    // This is to avoid 'NS_BASE_STREAM_CLOSED' exception that may occurs
    // See bug #188328.
    for (var i = 0; i < size; i++) {
      var c = this.stream.read(1);
      c ? postString += c : postString += '\0';
    }
  } catch (ex) {
    console.log("Error parsing the POST request", ex);
    return "";
  } finally {
    this.rewind();
  }

  // strip off trailing \r\n's
  while (postString.indexOf("\r\n") == (postString.length - 2)) {
    postString = postString.substring(0, postString.length - 2);
  }
  this.postBody = postString.trim();
};

exports.HttpPostParser = HttpPostParser;
