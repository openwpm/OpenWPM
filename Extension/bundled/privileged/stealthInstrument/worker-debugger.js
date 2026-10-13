/**
 * Prototype: runs in a dedicated worker's debugger global
 * (WorkerDebuggerGlobalScope), ahead of the worker's main script.
 *
 * The debugger global has the worker's principal, but every wrapper between it
 * and the worker global is opaque (`Wrap` in dom/workers/RuntimeService.cpp):
 * it can neither read the worker's prototypes nor hand the worker a callable.
 * So `workerRealm` is evaluated INSIDE the worker global through
 * `Debugger.Object.executeInGlobal`, which needs a global reference but no
 * debuggee: the worker never enters debug mode. Its records are pulled back
 * through `Debugger.Object.call` and posted to the main thread.
 */

/* global Debugger */
"use strict";

// The worker sees this URL in every stack that crosses an instrumented member.
const REALM_URL =
  "resource://openwpm/privileged/stealthInstrument/worker-realm.js";

const dbg = new Debugger();
let drain = null;

function describe(completion) {
  if (!completion) {
    return "terminated";
  }
  const error = completion.throw;
  return error && typeof error === "object"
    ? String(error.getProperty("message")?.return ?? error.class)
    : String(error);
}

function install(surface) {
  const worker = dbg.makeGlobalObjectReference(global);
  const completion = worker.executeInGlobal(
    `(${workerRealm})(${JSON.stringify(surface)}, ${JSON.stringify(REALM_URL)})`,
    { url: REALM_URL },
  );
  if (completion && "return" in completion) {
    drain = completion.return;
  } else {
    reportError("OpenWPM: worker instrument failed: " + describe(completion));
  }
}

function flush() {
  if (!drain) {
    return;
  }
  const completion = drain.call(undefined);
  const batch = completion?.return;
  if (typeof batch === "string" && batch) {
    postMessage(batch);
  } else if (!completion || "throw" in completion) {
    reportError("OpenWPM: worker drain failed: " + describe(completion));
  }
}

addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.install) {
    install(message.install);
  } else if (message.drain) {
    flush();
  }
});

/**
 * Evaluated in the worker global, by source: it must not close over anything
 * here. Page script runs in this realm afterwards and can replace any builtin,
 * so the hot path only calls intrinsics captured now, through `apply`, and only
 * builds null-prototype objects.
 */
function workerRealm(surface, ownUrl) {
  "use strict";
  const apply = Reflect.apply;
  const defineProperty = Object.defineProperty;
  const getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
  const getOwnPropertyNames = Object.getOwnPropertyNames;
  const setPrototypeOf = Object.setPrototypeOf;
  const isArray = Array.isArray;
  const stringify = JSON.stringify;
  const StringCtor = String;
  const ErrorCtor = Error;
  const DateCtor = Date;
  const stackGetter = getOwnPropertyDescriptor(Error.prototype, "stack").get;
  const toISOString = Date.prototype.toISOString;
  const indexOf = String.prototype.indexOf;
  const lastIndexOf = String.prototype.lastIndexOf;
  const slice = String.prototype.slice;
  const MAX_LOG_COUNT = 500;
  const MAX_STRING = 65536;

  let pending = "";
  let ordinal = 0;
  const counts = { __proto__: null };

  function truncate(value) {
    return value.length > MAX_STRING
      ? apply(slice, value, [0, MAX_STRING]) + "TRUNCATED"
      : value;
  }

  // Page objects (arguments) are never read: any read can run a page getter or
  // Proxy trap. Arrays a native returned (navigator.languages) are copied.
  // Descriptors are null-prototype, or a page `Object.prototype.get` would run.
  function plain(value, native) {
    switch (typeof value) {
      case "string":
        return truncate(value);
      case "number":
      case "boolean":
      case "undefined":
        return value;
      case "symbol":
        return StringCtor(value);
      case "bigint":
        return StringCtor(value) + "n";
      case "function":
        return "FUNCTION";
    }
    if (value === null) {
      return "null";
    }
    if (native && isArray(value)) {
      const length = getOwnPropertyDescriptor(value, "length").value;
      const copy = [];
      setPrototypeOf(copy, null);
      for (let i = 0; i < length && i < 128; i++) {
        const element = getOwnPropertyDescriptor(value, i)?.value;
        defineProperty(copy, i, {
          __proto__: null,
          value: typeof element === "object" ? "object" : element,
          enumerable: true,
          writable: true,
          configurable: true,
        });
      }
      return stringify(copy);
    }
    return "object";
  }

  // "name@url:line:col"; the first frame outside this script is the caller.
  function callContext() {
    const stack = apply(stackGetter, new ErrorCtor(), []);
    let start = 0;
    while (start < stack.length) {
      let end = apply(indexOf, stack, ["\n", start]);
      if (end === -1) {
        end = stack.length;
      }
      const frame = apply(slice, stack, [start, end]);
      const at = apply(indexOf, frame, ["@"]);
      const location = apply(slice, frame, [at + 1]);
      if (at !== -1 && apply(indexOf, location, [ownUrl]) !== 0) {
        const colon = apply(lastIndexOf, location, [":"]);
        const lineColon = apply(lastIndexOf, location, [":", colon - 1]);
        return {
          __proto__: null,
          scriptUrl: apply(slice, location, [0, lineColon]),
          scriptLine: apply(slice, location, [lineColon + 1, colon]),
          scriptCol: apply(slice, location, [colon + 1]),
          funcName: apply(slice, frame, [0, at]),
        };
      }
      start = end + 1;
    }
    return {
      __proto__: null,
      scriptUrl: "",
      scriptLine: "",
      scriptCol: "",
      funcName: "",
    };
  }

  function record(type, operation, symbol, value, args) {
    const context = callContext();
    const key = context.scriptUrl + "|" + symbol;
    const count = counts[key] ?? 0;
    if (count >= MAX_LOG_COUNT) {
      return;
    }
    counts[key] = count + 1;
    const data = {
      __proto__: null,
      operation,
      symbol,
      value,
      args,
      scriptUrl: context.scriptUrl,
      scriptLine: context.scriptLine,
      scriptCol: context.scriptCol,
      funcName: context.funcName,
      scriptLocEval: "",
      callStack: "",
      ordinal: ordinal++,
      timeStamp: apply(toISOString, new DateCtor(), []),
    };
    const json = stringify({ __proto__: null, type, data });
    pending = pending === "" ? json : pending + "," + json;
  }

  function argsOf(list) {
    const out = [];
    setPrototypeOf(out, null);
    for (let i = 0; i < list.length; i++) {
      defineProperty(out, i, {
        __proto__: null,
        value: plain(list[i], false),
        enumerable: true,
        writable: true,
        configurable: true,
      });
    }
    return out;
  }

  // Native `name`, `length` and their order (a scripted function lists
  // `length` first); method definitions are not constructors.
  function shape(forwarder, native, name) {
    const length = getOwnPropertyDescriptor(native, "length").value;
    delete forwarder.length;
    delete forwarder.name;
    defineProperty(forwarder, "name", { value: name, configurable: true });
    defineProperty(forwarder, "length", { value: length, configurable: true });
    return forwarder;
  }

  function wrapMethod(native, name, symbol) {
    const forwarder = {
      [name]() {
        try {
          record("logCall", "call", symbol, "", argsOf(arguments));
        } catch {
          // never surface instrumentation failures
        }
        return apply(native, this, arguments);
      },
    }[name];
    return shape(forwarder, native, name);
  }

  function wrapGetter(native, name, symbol) {
    const getter = getOwnPropertyDescriptor(
      {
        get [name]() {
          const value = apply(native, this, []);
          try {
            record("logValue", "get", symbol, plain(value, true));
          } catch {
            // never surface instrumentation failures
          }
          return value;
        },
      },
      name,
    ).get;
    return shape(getter, native, "get " + name);
  }

  function wrapSetter(native, name, symbol) {
    const setter = getOwnPropertyDescriptor(
      {
        set [name](value) {
          try {
            record("logValue", "set", symbol, plain(value, false));
          } catch {
            // never surface instrumentation failures
          }
          apply(native, this, [value]);
        },
      },
      name,
    ).set;
    return shape(setter, native, "set " + name);
  }

  for (const { object, properties, excluded } of surface) {
    const proto = globalThis[object]?.prototype;
    if (!proto) {
      continue;
    }
    for (const name of properties ?? getOwnPropertyNames(proto)) {
      const descriptor = getOwnPropertyDescriptor(proto, name);
      if (!descriptor || name === "constructor" || excluded.includes(name)) {
        continue;
      }
      const symbol = object + "." + name;
      if (typeof descriptor.value === "function") {
        descriptor.value = wrapMethod(descriptor.value, name, symbol);
      } else if (descriptor.get || descriptor.set) {
        if (descriptor.get) {
          descriptor.get = wrapGetter(descriptor.get, name, symbol);
        }
        if (descriptor.set) {
          descriptor.set = wrapSetter(descriptor.set, name, symbol);
        }
      } else {
        continue;
      }
      defineProperty(proto, name, descriptor);
    }
  }

  return function drainRecords() {
    const batch = pending;
    pending = "";
    return batch === "" ? "" : "[" + batch + "]";
  };
}
