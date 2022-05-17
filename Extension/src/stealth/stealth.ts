"use strict";
/* Taken from https://github.com/kkapsner/CanvasBlocker with small changes
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { startInstrument as instrument,
         exportCustomFunction } from "./instrument";

// Declaring some local trackers
const interceptedWindows = new WeakMap();
const proxies = new Map();
const changedToStrings = new WeakMap();

// Entry point for this extension
(function(){
  // console.log("Starting frame script");
  try{
    interceptWindow(window);
  } catch (error) {
    console.log("Instrumentation initialisation crashed. Reason: " + error);
    console.log(error.stack);
  }
  // console.log("Starting frame script");
})();


function interceptWindow(context){
	let wrappedTry;
	try {
		const href = context.location.href;
		wrappedTry = getWrapped(context);
	}	catch (error){
		// we are unable to read the location due to SOP
		// therefore we also can not intercept anything.
		//console.log("NOT intercepting window due to SOP: ", context);
		return false;
	}
	const wrappedWindow = wrappedTry;

	if (interceptedWindows.get(wrappedWindow)){
    //console.log("Already intercepted: ", context);
		return false;
	}
	// console.log("intercepting window", context);
  instrument(context);
  interceptedWindows.set(wrappedWindow, true);

	//console.log("prepare to intercept "+ context.length +" (i)frames.");
	function interceptAllFrames(){
		const currentLength = context.length;
		for (let i = currentLength; i--;){
			if (!interceptedWindows.get(wrappedWindow[i])){
				interceptWindow(context[i]);
			}
		}
	}
  protectAllFrames(context, wrappedWindow, interceptWindow, interceptAllFrames);
  return true;
}

function protectAllFrames(context, wrappedWindow, singleCallback, allCallback){
		const changeWindowProperty = createChangeProperty(context);
		if (!changeWindowProperty){
			return;
		}

		const api = {context, wrappedWindow, changeWindowProperty, singleCallback, allCallback};

		protectFrameProperties(api);

		protectDOMModifications(api);

		// MutationObserver to intercept iFrames while generating the DOM.
		api.observe = enableMutationObserver(api);

		// MutationObserver does not trigger fast enough when document.write is used
		protectDocumentWrite(api);

    protectWindowOpen(api);
	};

function getWrapped(context) {
  return context && (context.wrappedJSObject || context);
}


function createChangeProperty(window){
	const changeWindowProperty = function (object, name, type, changed){
		const descriptor = Object.getOwnPropertyDescriptor(object, name);
		const original = descriptor[type];
		if ((typeof changed) === "function"){
			changed = createProxyFunction(window, original, changed);
		}
		changePropertyFunc(window, {object, name, type, changed});
	}
	return changeWindowProperty;
}

function createProxyFunction(context, original, replacement){
	if (!changedToStrings.get(context)){
		changedToStrings.set(context, true);
		const functionPrototype = getWrapped(context).Function.prototype;
		const toString = functionPrototype.toString;
		changePropertyFunc(
      context,
       {
         object: functionPrototype,
         name: "toString",
         type: "value",
         changed: createProxyFunction(
           context,
           toString,
           function(){
             return proxies.get(this) || toString.call(this);
				   }
			   )
      }
    );
	}
	const handler = getWrapped(context).Object.create(null);
	handler.apply = exportCustomFunction(function(target, thisArgs, args){
		try {
			return args.length?
				replacement.call(thisArgs, ...args):
				replacement.call(thisArgs);
		}
		catch (error){
			try {
				return original.apply(thisArgs, args);
			}
			catch (error){
				return target.apply(thisArgs, args);
			}
		}
	}, context, "");
	const proxy = new context.Proxy(original, handler);
	proxies.set(proxy, original.toString());
	return getWrapped(proxy);
};

function changePropertyFunc(context, {object, name, type, changed}){
  // Removed tracker for changed properties
	const descriptor = Object.getOwnPropertyDescriptor(object, name);
	const original = descriptor[type];
	descriptor[type] = changed;
	Object.defineProperty(object, name, descriptor);
};


function protectFrameProperties({context, wrappedWindow, changeWindowProperty, singleCallback}){
  ["HTMLIFrameElement", "HTMLFrameElement"].forEach(function(constructorName){
    const constructor = context[constructorName];
    const wrappedConstructor = wrappedWindow[constructorName];

    const contentWindowDescriptor = Object.getOwnPropertyDescriptor(
      constructor.prototype,
      "contentWindow"
    );
    //TODO: Continue here!!!!
    const originalContentWindowGetter = contentWindowDescriptor.get;
    const contentWindowTemp = {
      get contentWindow(){
        const window = originalContentWindowGetter.call(this);
        if (window){
          singleCallback(window);
        }
        return window;
      }
    };
    changeWindowProperty(wrappedConstructor.prototype, "contentWindow", "get",
      Object.getOwnPropertyDescriptor(contentWindowTemp, "contentWindow").get
    );

    const contentDocumentDescriptor = Object.getOwnPropertyDescriptor(
      constructor.prototype,
      "contentDocument"
  	);
  	const originalContentDocumentGetter = contentDocumentDescriptor.get;
  	const contentDocumentTemp = {
  		get contentDocument(){
        const document = originalContentDocumentGetter.call(this);
        if (document){
          singleCallback(document.defaultView);
        }
  			return document;
  		}
  	};
  	changeWindowProperty(wrappedConstructor.prototype, "contentDocument", "get",
  		Object.getOwnPropertyDescriptor(contentDocumentTemp, "contentDocument").get
  	);
  });
}

function protectDOMModifications({context, wrappedWindow, changeWindowProperty, allCallback}){
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
			setters: []
		},
		{
			object: wrappedWindow.Element.prototype,
			methods: [
				"append", "prepend",
				"insertAdjacentElement", "insertAdjacentHTML", "insertAdjacentText",
				"replaceWith"
			],
			getters: [],
			setters: [
				"innerHTML",
				"outerHTML"
			]
		}
	].forEach(function(protectionDefinition){
		const object = protectionDefinition.object;
		protectionDefinition.methods.forEach(function(method){
			const descriptor = Object.getOwnPropertyDescriptor(object, method);
			const original = descriptor.value;
			changeWindowProperty(object, method, "value", class {
				[method](){
					const value = arguments.length?
						original.call(this, ...arguments):
						original.call(this);
					allCallback();
					return value;
				}
			}.prototype[method]);
		});
		protectionDefinition.getters.forEach(function(property){
			const temp = {
				get [property](){
					const ret = this[property];
					allCallback();
					return ret;
				}
			};
			changeWindowProperty(object, property, "get",
				Object.getOwnPropertyDescriptor(temp, property).get
			);
		});
		protectionDefinition.setters.forEach(function(property){
			const descriptor = Object.getOwnPropertyDescriptor(object, property);
			const setter = descriptor.set;
			const temp = {
				set [property](value){
					const ret = setter.call(this, value);
					allCallback();
					return ret;
				}
			};
			changeWindowProperty(object, property, "set",
				Object.getOwnPropertyDescriptor(temp, property).set
			);
		});
	});
}

function enableMutationObserver({context, allCallback}){
	const observer = new MutationObserver(allCallback);
	let observing = false;
	function observe(){
		if (
			!observing &&
			context.document
		){
			observer.observe(context.document, {subtree: true, childList: true});
			observing = true;
		}
	}
	observe();
	context.document.addEventListener("DOMContentLoaded", function(){
		if (observing){
			observer.disconnect();
			observing = false;
		}
	});
	return observe;
}

function protectDocumentWrite({context, wrappedWindow, changeWindowProperty, observe, allCallback}){
	const documentWriteDescriptorOnHTMLDocument = Object.getOwnPropertyDescriptor(
		wrappedWindow.HTMLDocument.prototype,
		"write"
	);
	const documentWriteDescriptor = documentWriteDescriptorOnHTMLDocument || Object.getOwnPropertyDescriptor(
		wrappedWindow.Document.prototype,
		"write"
	);
	const documentWrite = documentWriteDescriptor.value;
	changeWindowProperty(
		documentWriteDescriptorOnHTMLDocument?
			wrappedWindow.HTMLDocument.prototype:
			wrappedWindow.Document.prototype,
		"write", "value", function write(markup){
			for (let i = 0, l = arguments.length; i < l; i += 1){
				const str = "" + arguments[i];
				// weird problem with waterfox and google docs
				const parts = (
					str.match(/^\s*<!doctype/i) &&
					!str.match(/frame/i)
				)? [str]: str.split(/(?=<)/);
				const length = parts.length;
				const scripts = context.document.getElementsByTagName("script");
				for (let i = 0; i < length; i += 1){
					documentWrite.call(this, parts[i]);
					allCallback();
					if (scripts.length && scripts[scripts.length - 1].src){
						observe();
					}
				}
			}
		}
	);

	const documentWritelnDescriptorOnHTMLDocument = Object.getOwnPropertyDescriptor(
		wrappedWindow.HTMLDocument.prototype,
		"writeln"
	);
	const documentWritelnDescriptor = documentWritelnDescriptorOnHTMLDocument || Object.getOwnPropertyDescriptor(
		wrappedWindow.Document.prototype,
		"writeln"
	);
	const documentWriteln = documentWritelnDescriptor.value;
	changeWindowProperty(
		documentWritelnDescriptorOnHTMLDocument?
			wrappedWindow.HTMLDocument.prototype:
			wrappedWindow.Document.prototype,
		"writeln", "value", function writeln(markup){
			for (let i = 0, l = arguments.length; i < l; i += 1){
				const str = "" + arguments[i];
				const parts = str.split(/(?=<)/);
				const length = parts.length;
				const scripts = context.document.getElementsByTagName("script");
				for (let i = 0; i < length; i += 1){
					documentWrite.call(this, parts[i]);
					allCallback();
					if (scripts.length && scripts[scripts.length - 1].src){
						observe();
					}
				}
			}
			documentWriteln.call(this, "");
		}
	);
}

function protectWindowOpen({context, wrappedWindow, changeWindowProperty, singleCallback}){
	const windowOpenDescriptor = Object.getOwnPropertyDescriptor(
		wrappedWindow,
		"open"
	);
	const windowOpen = windowOpenDescriptor.value;
	const getDocument = Object.getOwnPropertyDescriptor(
		context,
		"document"
	).get;
	changeWindowProperty(
		wrappedWindow,
		"open", "value", function open(){
			const newWindow = arguments.length?
				windowOpen.call(this, ...arguments):
				windowOpen.call(this);
			if (newWindow){
				// if we use windowOpen from the normal window we see some SOP errors
				// BUT we need the unwrapped window...
				singleCallback(getDocument.call(newWindow).defaultView);
			}
			return newWindow;
		}
	);
}

