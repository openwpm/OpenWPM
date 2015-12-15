function getPageScript() {

  // code below is not a content script: no Firefox APIs //////////////////////

  // return a string
  return "(" + function () {

    var event_id = document.currentScript.getAttribute('data-event-id');

    // from https://github.com/csnover/TraceKit/blob/b76ad786f84ed0c94701c83d8963458a8da54d57/tracekit.js#L641
    var geckoCallSiteRe = /^\s*(.*?)(?:\((.*?)\))?@?((?:file|https?|chrome):.*?):(\d+)(?::(\d+))?\s*$/i;

    // from Underscore v1.6.0
    function debounce(func, wait, immediate) {
      var timeout, args, context, timestamp, result;

      var later = function () {
        var last = Date.now() - timestamp;
        if (last < wait) {
          timeout = setTimeout(later, wait - last);
        } else {
          timeout = null;
          if (!immediate) {
            result = func.apply(context, args);
            context = args = null;
          }
        }
      };

      return function () {
        context = this;
        args = arguments;
        timestamp = Date.now();
        var callNow = immediate && !timeout;
        if (!timeout) {
          timeout = setTimeout(later, wait);
        }
        if (callNow) {
          result = func.apply(context, args);
          context = args = null;
        }

        return result;
      };
    }

    // messages the injected script
    var send = (function () {
      var messages = [];

      // debounce sending queued messages
      var _send = debounce(function () {
        document.dispatchEvent(new CustomEvent(event_id, {
          detail: messages
        }));

        // clear the queue
        messages = [];
      }, 100);

      return function (msg) {
        // queue the message
        messages.push(msg);

        _send();
      };
    }());

    function getStackTrace() {
      var stack;

      try {
        throw new Error();
      } catch (err) {
        stack = err.stack;
      }

      return stack;
    }

    function getOriginatingScriptUrl() {
      var trace = getStackTrace().split('\n');

      if (trace.length < 4) {
        return '';
      }

      // this script is at 0, 1 and 2
      var callSite = trace[3];

      var scriptUrlMatches = callSite.match(geckoCallSiteRe);
      return scriptUrlMatches && scriptUrlMatches[3] || '';
    }

    function trapInstanceMethod(item) {
      var is_canvas_write = (
        item.propName == 'fillText' || item.propName == 'strokeText'
      );

      item.obj[item.propName] = (function (orig) {

        return function () {
          var args = arguments;

          if (is_canvas_write) {
            // to avoid false positives,
            // bail if the text being written is too short
            if (!args[0] || args[0].length < 5) {
              return orig.apply(this, args);
            }
          }

          var script_url = getOriginatingScriptUrl(),
            msg = {
              obj: item.objName,
              prop: item.propName,
              scriptUrl: script_url
            };

          if (item.hasOwnProperty('extra')) {
            msg.extra = item.extra.apply(this, args);
          }

          send(msg);

          if (is_canvas_write) {
            // optimization: one canvas write is enough,
            // restore original write method
            // to this CanvasRenderingContext2D object instance
            this[item.propName] = orig;
          }

          return orig.apply(this, args);
        };

      }(item.obj[item.propName]));
    }

    var methods = [];

    ['getImageData', 'fillText', 'strokeText'].forEach(function (method) {
      var item = {
        objName: 'CanvasRenderingContext2D.prototype',
        propName: method,
        obj: CanvasRenderingContext2D.prototype,
        extra: function () {
          return {
            canvas: true
          };
        }
      };

      if (method == 'getImageData') {
        item.extra = function () {
          var args = arguments,
            width = args[2],
            height = args[3];

          // "this" is a CanvasRenderingContext2D object
          if (width === undefined) {
            width = this.canvas.width;
          }
          if (height === undefined) {
            height = this.canvas.height;
          }

          return {
            canvas: true,
            width: width,
            height: height
          };
        };
      }

      methods.push(item);
    });

    methods.push({
      objName: 'HTMLCanvasElement.prototype',
      propName: 'toDataURL',
      obj: HTMLCanvasElement.prototype,
      extra: function () {
        // "this" is a canvas element
        return {
          canvas: true,
          width: this.width,
          height: this.height
        };
      }
    });

    methods.forEach(trapInstanceMethod);

  } + "());";

  // code above is not a content script: no Firefox APIs //////////////////////

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

var event_id = Math.random();

// listen for messages from the script we are about to insert
document.addEventListener(event_id, function (e) {
  // pass these on to the background page
  self.port.emit('fpReport', e.detail);
});

insertScript(getPageScript(), {
  event_id: event_id
});
