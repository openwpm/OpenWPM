/**
 * Makes `navigator.webdriver` read as `false` in every content realm.
 *
 * Runs in the content process with chrome privileges, driven by the
 * `content-document-global-created` observer notification, which fires
 * synchronously as each window global is created -- before any script in that
 * realm, and before the parent task that created a frame continues.
 *
 * Nothing in the content realm is hooked to achieve this. The page's own
 * `Navigator.prototype.webdriver` accessor is replaced with one compiled in the
 * page's compartment via `Cu.exportFunction`, so it reports `[native code]`
 * under the native accessor name and the rest of the descriptor is reused
 * unchanged. `HTMLIFrameElement.prototype` and friends are left alone, so this
 * adds no page-observable surface of its own.
 */

export class OpenWPMWebdriverSpoofChild extends JSWindowActorChild {
  observe(subject, topic) {
    if (topic !== "content-document-global-created") {
      return;
    }
    try {
      spoofNavigatorWebdriver(subject);
    } catch (error) {
      console.error("OpenWPM: failed to spoof navigator.webdriver", error);
    }
  }
}

function spoofNavigatorWebdriver(win) {
  if (!win) {
    return;
  }
  // Leave privileged and extension documents alone; only content is measured.
  const principal = win.document?.nodePrincipal;
  if (!principal || principal.isSystemPrincipal || principal.addonPolicy) {
    return;
  }

  const pageWindow = win.wrappedJSObject;
  const navigatorPrototype = pageWindow?.Navigator?.prototype;
  if (!navigatorPrototype) {
    return;
  }
  const descriptor = Object.getOwnPropertyDescriptor(
    navigatorPrototype,
    "webdriver",
  );
  if (!descriptor?.get) {
    return;
  }
  // `defineAs` names the page-side function, so the page sees the native
  // accessor name "get webdriver". The throwaway null-prototype holder keeps
  // the function off any object the page can reach.
  const nativeGetter = descriptor.get;
  const spoofedGetter = Cu.exportFunction(
    function () {
      // Delegate receiver validation to the native getter rather than
      // reimplementing it: called on anything that is not a Navigator this
      // throws exactly what the page would otherwise have seen, down to the
      // message. Its return value is what we are replacing, so discard it.
      nativeGetter.call(this);
      return false;
    },
    pageWindow.Object.create(null),
    { defineAs: "get webdriver" },
  );
  // `exportFunction` installs `name` before `length`; a native accessor reports
  // them the other way round, and `Object.getOwnPropertyNames` exposes the
  // difference. Both are configurable, so redefine them in the native order.
  const nameDescriptor = Object.getOwnPropertyDescriptor(spoofedGetter, "name");
  const lengthDescriptor = Object.getOwnPropertyDescriptor(
    spoofedGetter,
    "length",
  );
  delete spoofedGetter.name;
  delete spoofedGetter.length;
  Object.defineProperty(spoofedGetter, "length", lengthDescriptor);
  Object.defineProperty(spoofedGetter, "name", nameDescriptor);
  Object.defineProperty(navigatorPrototype, "webdriver", {
    ...descriptor,
    get: spoofedGetter,
  });
}
