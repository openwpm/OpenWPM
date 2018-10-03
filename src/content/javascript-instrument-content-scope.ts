import { pageScript } from "./javascript-instrument-page-scope";

function getPageScriptAsString() {
  // return a string
  return "(" + pageScript + "());";
}


function insertScript(text, data) {
  var parent = document.documentElement,
    script = document.createElement('script');
  script.text = text;
  script.async = false;

  for (var key in data) {
    script.setAttribute('data-' + key.replace('_', '-'), data[key]);
  }

  parent.insertBefore(script, parent.firstChild);
  parent.removeChild(script);
}

function emitMsg(type, msg) {
  msg.timeStamp = new Date().toISOString();
  browser.runtime.sendMessage({namespace: 'javascript-instrumentation', type, data: msg})
    .catch(function(err) {
      console.log("OpenWPM content to background script 'emitMsg' sendMessage failed");
      console.error(err);
    });
}

var event_id = Math.random();

// listen for messages from the script we are about to insert
document.addEventListener(event_id, function (e) {
  // pass these on to the background page
  var msgs = e.detail;
  if (Array.isArray(msgs)) {
    msgs.forEach(function (msg) {
      emitMsg(msg['type'],msg['content']);
    });
  } else {
    emitMsg(msgs['type'],msgs['content']);
  }
});

export function run(testing) {
  insertScript(getPageScriptAsString(), {
    event_id: event_id,
    testing: testing,
  });
}
