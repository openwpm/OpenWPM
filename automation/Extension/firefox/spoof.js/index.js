/*
/* This code to spoof values of the `window.navigator` object using a
 * JavaScript proxy is based on:
 * User Agent Switcher
 * Copyright © 2017 – 2019  Alexander Schlarb (https://gitlab.com/ntninja)
/* For the used part see: https://gitlab.com/ntninja/user-agent-switcher/blob/6aacc15ed6651317776f7abb3a85d6f34fc1a254/content/override-navigator-data.js
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
        return Reflect.get(origNavigator, prop);
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

spoofNavigator(window);
