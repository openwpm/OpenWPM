/**
 * This code to spoof values of the `window.navigator` object using a
 * JavaScript proxy is based on:
 * User Agent Switcher
 * Copyright © 2017 – 2019 Alexander Schlarb (https://gitlab.com/ntninja)
 * For the used part see: https://gitlab.com/ntninja/user-agent-switcher/blob/6aacc15ed6651317776f7abb3a85d6f34fc1a254/content/override-navigator-data.js
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * Set of all object that we have already proxied to prevent them from being
 * proxied twice.
 */
let proxiedObjects = new Set();

/**
 * Convenience wrapped around `cloneInto` that enables all possible cloning
 * options by default.
 */
function cloneIntoFull(value, scope) {
	return cloneInto(value, scope, {
		cloneFunctions: true,
		wrapReflectors: true
	});
}

/**
 * Spoof `navigator` by overwriting the `navigator` of the given
 * (content script scope) `window` object with a proxy, if applicable.
 */
function spoofNavigator(window) {
	if (!(window instanceof Window)) { // Not actually a window object
		return window;
	}

	let origNavigator = window.navigator.wrappedJSObject; // `navigator` of the page scope
	if (proxiedObjects.has(origNavigator)) { // Window was already shadowed
		return window;
	}

	let spoofedGet_PageScope = cloneIntoFull({
		get: (target, prop, receiver) => {
			if (prop === "webdriver") {
				return false;
			} else {
				let value = Reflect.get(origNavigator, prop);
				if(typeof(value) === "function") { // Bind functions like `navigator.javaEnabled()` to the orginal object in the page scope to allow them to execute
					let boundFunc = Function.prototype.bind.call(value, origNavigator); // `value` is used as `this` to call the `bind` function that creates a copy of `Function.prototype` that always runs in the `this` context `origiNavigator`
					value = cloneIntoFull(boundFunc, window.wrappedJSObject);
				}
				return value;
			}
		}
	}, window.wrappedJSObject); // The `get` function, defined in privileged code (that is here in the extension / content script), is cloned into the target scope (that is the web page / `window.wrappedJSObject`) and thus accessible there. The return value is the reference to the cloned object in the defined scope.

	let origProxy = window.wrappedJSObject.Proxy;
	let navigatorProxy = new origProxy(origNavigator, spoofedGet_PageScope);

	proxiedObjects.add(origNavigator);

	let returnFunc_PageScope = exportFunction(() => {
		return navigatorProxy;
	}, window.wrappedJSObject);
	// Using `__defineGetter__` here our function gets assigned the correct
	// name of `get navigator`. Additionally its property descriptor has
	// no `set` function and will silently ignore any assigned value. – This
	// exact configuration is not achievable using `Object.defineProperty`.
	Object.prototype.__defineGetter__.call(window.wrappedJSObject, "navigator", returnFunc_PageScope);
	return window;
}

/**
 * Override `navigator` with the given data on the given page scoped `window`
 * object if applicable
 *
 * This will convert the given `window` object to being content-script scoped
 * after checking whether it can be converted at all or is just a restricted
 * accessor that does not grant access to anything important.
 */
function spoofNavigatorFromPageScope(unsafeWindow) {
	if(!(unsafeWindow instanceof Window)) {
		return unsafeWindow; // Not actually a window object
	}
	
	try {
		unsafeWindow.navigator; // This will throw if this is a cross-origin frame
		
		let windowObj = cloneIntoFull(unsafeWindow, window);
		return spoofNavigator(windowObj).wrappedJSObject;
	} catch(e) {
		if(e instanceof DOMException && e.name == "SecurityError") {
			// Ignore error created by accessing a cross-origin frame and
			// just return the restricted frame (`navigator` is inaccessible
			// on these so there is nothing to patch)
			return unsafeWindow;
		} else {
			throw e;
		}
	}
}


spoofNavigator(window);

// Use some prototype hacking to prevent access to the original `navigator`
// through the IFrame leak
const IFRAME_TYPES = Object.freeze([HTMLFrameElement, HTMLIFrameElement]);
for(let type of IFRAME_TYPES) {
	// Get reference to contentWindow & contentDocument accessors into the
	// content script scope
	let contentWindowGetter = Reflect.getOwnPropertyDescriptor(
		type.prototype.wrappedJSObject, "contentWindow"
	).get;
	contentWindowGetter = cloneIntoFull(contentWindowGetter, window);
	let contentDocumentGetter = Reflect.getOwnPropertyDescriptor(
		type.prototype.wrappedJSObject, "contentDocument"
	).get;
	contentDocumentGetter = cloneIntoFull(contentDocumentGetter, window);
	
	// Export compatible accessor on the property that patches the navigator
	// element before returning
	Object.prototype.__defineGetter__.call(type.prototype.wrappedJSObject, "contentWindow",
			exportFunction(function () {
				let contentWindow = contentWindowGetter.call(this);
				return spoofNavigatorFromPageScope(contentWindow);
			}, window.wrappedJSObject)
	);
	Object.prototype.__defineGetter__.call(type.prototype.wrappedJSObject, "contentDocument",
			exportFunction(function () {
				let contentDocument = contentDocumentGetter.call(this);
				if(contentDocument !== null) {
					spoofNavigatorFromPageScope(contentDocument.defaultView);
				}
				return contentDocument;
			}, window.wrappedJSObject)
	);
}

// Asynchrously track added IFrame elements and trigger their prototype
// properties defined above to ensure that they are patched
// (This is a best-effort workaround for us being unable to *properly* fix the `window[0]` case.)
let patchNodes = (nodes) => {
	for(let node of nodes) {
		let isNodeFrameType = false;
		for(let type of IFRAME_TYPES) {
			if(isNodeFrameType = (node instanceof type)){ break; }
		}
		if(!isNodeFrameType) {
			continue;
		}
		
		node.contentWindow;
		node.contentDocument;
	}
};
let observer = new MutationObserver((mutations) => {
	for(let mutation of mutations) {
		patchNodes(mutation.addedNodes);
	}
});
observer.observe(document.documentElement, {
	childList: true,
	subtree: true
});
patchNodes(document.querySelectorAll("frame,iframe"));

