"use strict";
/* Taken from https://github.com/kkapsner/CanvasBlocker with small changes
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  startInstrument as instrument,
  exportCustomFunction,
} from "./instrument";

// Declaring some local trackers
const interceptedWindows = new WeakMap();
// Keyed on the wrapping proxy (always an object); only ever read via .get/.set,
// never iterated — so a WeakMap suffices and lets entries be collected with
// their proxies instead of being retained for the document's lifetime.
const proxies = new WeakMap();
const changedToStrings = new WeakMap();
export type ModifiedWindow = Window &
  typeof globalThis & { wrappedJSObject: any };
// Entry point for this extension
(function () {
  // console.log("Starting frame script");
  try {
    interceptWindow(window as ModifiedWindow);
  } catch (error) {
    console.log("Instrumentation initialisation crashed. Reason: " + error);
    console.log(error.stack);
  }
  // console.log("Starting frame script");
})();

function interceptWindow(context: ModifiedWindow) {
  let wrappedTry;
  try {
    wrappedTry = getWrapped(context);
  } catch {
    // we are unable to read the location due to SOP
    // therefore we also can not intercept anything.
    // console.log("NOT intercepting window due to SOP: ", context);
    return false;
  }
  const wrappedWindow = wrappedTry;

  if (interceptedWindows.get(wrappedWindow)) {
    // console.log("Already intercepted: ", context);
    return false;
  }
  // console.log("intercepting window", context);
  instrument(context);
  interceptedWindows.set(wrappedWindow, true);

  // console.log("prepare to intercept "+ context.length +" (i)frames.");
  function interceptAllFrames() {
    const currentLength = context.length;
    for (let i = currentLength; i--; ) {
      if (!interceptedWindows.get(wrappedWindow[i])) {
        interceptWindow(context[i] as ModifiedWindow);
      }
    }
  }
  protectAllFrames(context, wrappedWindow, interceptWindow, interceptAllFrames);
  return true;
}

function protectAllFrames(context, wrappedWindow, singleCallback, allCallback) {
  const changeWindowProperty = createChangeProperty(context);
  if (!changeWindowProperty) {
    return;
  }

  const api = {
    context,
    wrappedWindow,
    changeWindowProperty,
    singleCallback,
    allCallback,
    observe: null,
  };

  protectFrameProperties(api);

  protectDOMModifications(api);

  // MutationObserver to intercept iFrames while generating the DOM.
  api.observe = enableMutationObserver(api);

  // MutationObserver does not trigger fast enough when document.write is used
  protectDocumentWrite(api);

  protectWindowOpen(api);
}

function getWrapped(
  context: Window & typeof globalThis & { wrappedJSObject: any },
) {
  return context && (context.wrappedJSObject || context);
}

function createChangeProperty(window) {
  const changeWindowProperty = function (object, name, type, changed) {
    const descriptor = Object.getOwnPropertyDescriptor(object, name);
    const original = descriptor[type];
    if (typeof changed === "function") {
      changed = createProxyFunction(window, original, changed);
    }
    changePropertyFunc(window, { object, name, type, changed });
  };
  return changeWindowProperty;
}

function createProxyFunction(context, original, replacement) {
  if (!changedToStrings.get(context)) {
    changedToStrings.set(context, true);
    const functionPrototype = getWrapped(context).Function.prototype;
    const toString = functionPrototype.toString;
    changePropertyFunc(context, {
      object: functionPrototype,
      name: "toString",
      type: "value",
      changed: createProxyFunction(context, toString, function () {
        return proxies.get(this) || toString.call(this);
      }),
    });
  }
  const handler = getWrapped(context).Object.create(null);
  handler.apply = exportCustomFunction(
    function (target, thisArgs, args) {
      try {
        return args.length
          ? replacement.call(thisArgs, ...args)
          : replacement.call(thisArgs);
      } catch {
        try {
          return original.apply(thisArgs, args);
        } catch {
          return target.apply(thisArgs, args);
        }
      }
    },
    context,
    "",
  );
  const proxy = new context.Proxy(original, handler);
  proxies.set(proxy, original.toString());
  return getWrapped(proxy);
}

function changePropertyFunc(_context, { object, name, type, changed }) {
  // Removed tracker for changed properties
  const descriptor = Object.getOwnPropertyDescriptor(object, name);
  descriptor[type] = changed;
  Object.defineProperty(object, name, descriptor);
}

function protectFrameProperties({
  context,
  wrappedWindow,
  changeWindowProperty,
  singleCallback,
}) {
  ["HTMLIFrameElement", "HTMLFrameElement"].forEach(function (constructorName) {
    const constructor = context[constructorName];
    const wrappedConstructor = wrappedWindow[constructorName];

    // This runs at document_start on every frame, including non-HTML or
    // otherwise restricted contexts where these constructors (or their
    // prototype property descriptors) may be absent. Skip gracefully rather
    // than throwing.
    if (!constructor || !constructor.prototype || !wrappedConstructor) {
      return;
    }

    const contentWindowDescriptor = Object.getOwnPropertyDescriptor(
      constructor.prototype,
      "contentWindow",
    );
    const originalContentWindowGetter =
      contentWindowDescriptor && contentWindowDescriptor.get;
    if (!originalContentWindowGetter) {
      return;
    }
    const contentWindowTemp = {
      get contentWindow() {
        const window = originalContentWindowGetter.call(this);
        if (window) {
          singleCallback(window);
        }
        return window;
      },
    };
    changeWindowProperty(
      wrappedConstructor.prototype,
      "contentWindow",
      "get",
      Object.getOwnPropertyDescriptor(contentWindowTemp, "contentWindow").get,
    );

    const contentDocumentDescriptor = Object.getOwnPropertyDescriptor(
      constructor.prototype,
      "contentDocument",
    );
    const originalContentDocumentGetter =
      contentDocumentDescriptor && contentDocumentDescriptor.get;
    if (!originalContentDocumentGetter) {
      return;
    }
    const contentDocumentTemp = {
      get contentDocument() {
        const document = originalContentDocumentGetter.call(this);
        if (document) {
          singleCallback(document.defaultView);
        }
        return document;
      },
    };
    changeWindowProperty(
      wrappedConstructor.prototype,
      "contentDocument",
      "get",
      Object.getOwnPropertyDescriptor(contentDocumentTemp, "contentDocument")
        .get,
    );
  });
}

function protectDOMModifications({
  wrappedWindow,
  changeWindowProperty,
  allCallback,
}) {
  [
    // useless as length could be obtained before the iframe is created and window.frames === window
    // {
    // 	object: wrappedWindow,
    // 	methods: [],
    // 	getters: ["length", "frames"],
    // 	setters: []
    // },
    {
      object: wrappedWindow.Node.prototype,
      methods: ["appendChild", "insertBefore", "replaceChild"],
      getters: [],
      setters: [],
    },
    {
      object: wrappedWindow.Element.prototype,
      methods: [
        "append",
        "prepend",
        "insertAdjacentElement",
        "insertAdjacentHTML",
        "insertAdjacentText",
        "replaceWith",
      ],
      getters: [],
      setters: ["innerHTML", "outerHTML"],
    },
  ].forEach(function (protectionDefinition) {
    const object = protectionDefinition.object;
    if (!object) {
      return;
    }
    protectionDefinition.methods.forEach(function (method) {
      const descriptor = Object.getOwnPropertyDescriptor(object, method);
      // Runs at document_start in arbitrary (incl. non-HTML) contexts where a
      // listed method may be absent or not a data-descriptor. Skip rather than
      // throwing, which would abort the rest of stealth setup for this frame.
      if (!descriptor || typeof descriptor.value !== "function") {
        return;
      }
      const original = descriptor.value;
      changeWindowProperty(
        object,
        method,
        "value",
        class {
          /* eslint-disable prefer-rest-params -- this replacement is wrapped by createProxyFunction in a Proxy whose target is the native `original`, so the page-visible `.length` is forwarded from that target (arity is preserved by the Proxy, not by this function's own signature). `arguments` is used here only to forward the variadic call to `original`; switching to rest params would not change observable arity but is avoided to keep the forwarding shape uniform with the other replacements. */
          [method]() {
            const value = arguments.length
              ? original.call(this, ...arguments)
              : original.call(this);
            allCallback();
            return value;
          }
          /* eslint-enable prefer-rest-params */
        }.prototype[method],
      );
    });
    protectionDefinition.getters.forEach(function (property) {
      const temp = {
        get [property]() {
          const ret = this[property];
          allCallback();
          return ret;
        },
      };
      changeWindowProperty(
        object,
        property,
        "get",
        Object.getOwnPropertyDescriptor(temp, property).get,
      );
    });
    protectionDefinition.setters.forEach(function (property) {
      const descriptor = Object.getOwnPropertyDescriptor(object, property);
      // The descriptor (or its setter) may be missing for some
      // properties/contexts; skip non-settable properties instead of throwing.
      if (!descriptor || !descriptor.set) {
        return;
      }
      const setter = descriptor.set;
      const temp = {
        set [property](value) {
          setter.call(this, value);
          allCallback();
        },
      };
      changeWindowProperty(
        object,
        property,
        "set",
        Object.getOwnPropertyDescriptor(temp, property).set,
      );
    });
  });
}

function enableMutationObserver({ context, allCallback }) {
  const observer = new MutationObserver(allCallback);
  let observing = false;
  function observe() {
    if (!observing && context.document) {
      observer.observe(context.document, { subtree: true, childList: true });
      observing = true;
    }
  }
  observe();
  if (context.document) {
    context.document.addEventListener("DOMContentLoaded", function () {
      if (observing) {
        observer.disconnect();
        observing = false;
      }
    });
  }
  return observe;
}

function protectDocumentWrite({
  context,
  wrappedWindow,
  changeWindowProperty,
  observe,
  allCallback,
}) {
  // Runs at document_start on every frame, including non-HTML / restricted
  // contexts where HTMLDocument (or the write/writeln descriptors) may be
  // absent. Resolve the prototypes defensively and bail out instead of
  // throwing, which would disable the rest of stealth setup for this frame.
  const htmlDocProto =
    wrappedWindow.HTMLDocument && wrappedWindow.HTMLDocument.prototype;
  const docProto = wrappedWindow.Document && wrappedWindow.Document.prototype;

  const documentWriteDescriptorOnHTMLDocument = htmlDocProto
    ? Object.getOwnPropertyDescriptor(htmlDocProto, "write")
    : undefined;
  const documentWriteDescriptor =
    documentWriteDescriptorOnHTMLDocument ||
    (docProto ? Object.getOwnPropertyDescriptor(docProto, "write") : undefined);
  if (
    !documentWriteDescriptor ||
    typeof documentWriteDescriptor.value !== "function"
  ) {
    return;
  }
  const documentWrite = documentWriteDescriptor.value;
  changeWindowProperty(
    documentWriteDescriptorOnHTMLDocument ? htmlDocProto : docProto,
    "write",
    "value",
    /* eslint-disable prefer-rest-params -- replaces native document.write via createProxyFunction, which wraps this in a Proxy over the native `original`; the page-visible `.length` comes from that Proxy target, not from this signature. `arguments` handles the variadic call; rest params are avoided only to keep the forwarding shape uniform. */
    function write(_markup) {
      for (let i = 0, l = arguments.length; i < l; i += 1) {
        const str = "" + arguments[i];
        // weird problem with waterfox and google docs
        const parts =
          str.match(/^\s*<!doctype/i) && !str.match(/frame/i)
            ? [str]
            : str.split(/(?=<)/);
        const length = parts.length;
        const scripts = context.document.getElementsByTagName("script");
        for (let i = 0; i < length; i += 1) {
          documentWrite.call(this, parts[i]);
          allCallback();
          if (scripts.length && scripts[scripts.length - 1].src) {
            observe();
          }
        }
      }
    },
    /* eslint-enable prefer-rest-params */
  );

  const documentWritelnDescriptorOnHTMLDocument = htmlDocProto
    ? Object.getOwnPropertyDescriptor(htmlDocProto, "writeln")
    : undefined;
  const documentWritelnDescriptor =
    documentWritelnDescriptorOnHTMLDocument ||
    (docProto
      ? Object.getOwnPropertyDescriptor(docProto, "writeln")
      : undefined);
  if (
    !documentWritelnDescriptor ||
    typeof documentWritelnDescriptor.value !== "function"
  ) {
    return;
  }
  const documentWriteln = documentWritelnDescriptor.value;
  changeWindowProperty(
    documentWritelnDescriptorOnHTMLDocument ? htmlDocProto : docProto,
    "writeln",
    "value",
    /* eslint-disable prefer-rest-params -- replaces native document.writeln via createProxyFunction, which wraps this in a Proxy over the native `original`; the page-visible `.length` comes from that Proxy target, not from this signature. `arguments` handles the variadic call; rest params are avoided only to keep the forwarding shape uniform. */
    function writeln(_markup) {
      for (let i = 0, l = arguments.length; i < l; i += 1) {
        const str = "" + arguments[i];
        const parts = str.split(/(?=<)/);
        const length = parts.length;
        const scripts = context.document.getElementsByTagName("script");
        for (let i = 0; i < length; i += 1) {
          documentWrite.call(this, parts[i]);
          allCallback();
          if (scripts.length && scripts[scripts.length - 1].src) {
            observe();
          }
        }
      }
      documentWriteln.call(this, "");
    },
    /* eslint-enable prefer-rest-params */
  );
}

function protectWindowOpen({
  context,
  wrappedWindow,
  changeWindowProperty,
  singleCallback,
}) {
  const windowOpenDescriptor = Object.getOwnPropertyDescriptor(
    wrappedWindow,
    "open",
  );
  const documentDescriptor = Object.getOwnPropertyDescriptor(
    context,
    "document",
  );
  // Defensive: in restricted contexts these descriptors may be missing. Skip
  // rather than throwing and aborting the rest of stealth setup.
  if (
    !windowOpenDescriptor ||
    typeof windowOpenDescriptor.value !== "function" ||
    !documentDescriptor ||
    !documentDescriptor.get
  ) {
    return;
  }
  const windowOpen = windowOpenDescriptor.value;
  const getDocument = documentDescriptor.get;
  /* eslint-disable prefer-rest-params -- replaces native window.open via createProxyFunction, which wraps this in a Proxy over the native `original`; the page-visible `.length` is forwarded from that Proxy target, not from this function's (zero-param) signature. `arguments` forwards the variadic call; rest params are avoided only to keep the forwarding shape uniform. */
  changeWindowProperty(wrappedWindow, "open", "value", function open() {
    const newWindow = arguments.length
      ? windowOpen.call(this, ...arguments)
      : windowOpen.call(this);
    if (newWindow) {
      // if we use windowOpen from the normal window we see some SOP errors
      // BUT we need the unwrapped window...
      singleCallback(getDocument.call(newWindow).defaultView);
    }
    return newWindow;
  });
  /* eslint-enable prefer-rest-params */
}
