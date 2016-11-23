// We don't know the order the content scripts will load
// so let's try to remove the attributes now (if they already exist)
// or register an event handler if they don't.
// * https://github.com/SeleniumHQ/selenium/blob/b82512999938d41f6765ce8017284dcabe437d4c/javascript/firefox-driver/extension/content/server.js#L49
// * https://github.com/SeleniumHQ/selenium/blob/b82512999938d41f6765ce8017284dcabe437d4c/javascript/firefox-driver/extension/content/dommessenger.js#L98
function getPageScript() {
  // return a string
  return "(" + function() {
    if ("webdriver" in navigator) {
      console.log("Webdriver attributes present, remove immediately");
      // Attributes can be removed immediately
      document.documentElement.removeAttribute("webdriver");
      delete window.navigator["webdriver"];
      console.log("Webdriver attributes removed!");
    } else {
      // Listener for `document` attribute
      document.addEventListener("DOMAttrModified", function monitor(ev) {
        console.log("Removing webdriver attribute from document");
        document.documentElement.removeAttribute("webdriver");
        document.removeEventListener("DOMAttrModified", monitor, false);
      }, false);

      // Prevent webdriver attribute from getting set on navigator
      var originalDefineProperty = Object.defineProperty;
      Object.defineProperty(Object, 'defineProperty', {
        value: function(obj, prop, descriptor) {
          if (obj == window.navigator && prop == 'webdriver') {
            console.log("Preventing definition of webdriver property on navigator.");

            // Return Object.defineProperty to original state
            Object.defineProperty(Object, 'defineProperty', {
              value: originalDefineProperty
            });
            return undefined;
          }
          return originalDefineProperty(obj, prop, descriptor);
        }
      });
      console.log("Webdriver attribute handlers started!");
    }
  } + "());";
}

function insertScript(text) {
  var parent = document.documentElement,
    script = document.createElement('script');
  script.text = text;
  script.async = false;

  parent.insertBefore(script, parent.firstChild);
  parent.removeChild(script);
}
insertScript(getPageScript());
