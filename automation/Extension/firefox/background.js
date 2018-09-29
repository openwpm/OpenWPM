var DEBUG = true;

/**
 * Kill the current tab and create a new one to stop traffic.
 */
function tab_restart_browser() {
    var current_url = window.location.href;
    window.close();
    window.open(current_url);
}

function browser_scroll(x_coord, y_coord) {
    window.scrollTo(x_coord, y_coord)
}

function listCookies() {
    return document.cookie.split(';');
}

function get_links_in_current_window() {
    var link_list = [];
    var links = document.links;
    for(var i = 0; i < links.length; i++) {
        link_list.push(links[i].href)
    }
    return link_list
}

function dump_page_source(url) {
    return document.documentElement.outerHTML
}

function reportJs(obj){
  console.log('reportjs', obj);
  if (!DEBUG) socket.emit('sql', { data: obj, type: 'js' });
  return true;
}

function reportProfile(obj){
  console.log('reportprofile', obj);
  if (!DEBUG) socket.emit('sql', { data: obj, type: 'cp' });
  return true;
}

function reportCookies(obj){
  console.log('reportcookies', obj);
  if (!DEBUG) socket.emit('sql', { data: obj, type: 'ck' });
  return true;
}

function setup(settings){
  if (settings[0]){
      chrome.cookies.onChanged.addListener(function(info){
          reportCookies(info);
      })
  }

  if (settings[1]) {

      chrome.webRequest.onCompleted.addListener(
          function(details) {
            reportProfile(details);
          },
          {urls: ["<all_urls>"]});
  }

  if (settings[2]) {
      chrome.runtime.onConnect.addListener(function(port) {
          console.assert(port.name == "javascriptMsg");
          port.onMessage.addListener(function(msg) {
              reportJs(msg);
          });
      });
  }
}

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    console.log(sender.tab ?
                "from a content script:" + sender.tab.url :
                "from the extension");
    if (request.greeting == "request_settings")
      sendResponse({settings: getSettings()});
  });


  // connect to websocket server
  if (DEBUG){
    setup([true,true,true]);
  } else {
    var socket = io('http://localhost:7331/openwpm');
    var is_setup = false;
    socket.on('config', function (data) {
      settings = [false, false, false];
      settings[0] = data['ck'];
      settings[1] = data['cp'];
      settings[2] = data['js'];
      if (!is_setup){
        console.log('config data',data);
        setup(settings);
        is_setup = true;
      }
    });
  }
