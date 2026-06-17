const settings = arguments[0];

function getPropertyNames(subject) {
  // Mirror Object.getPropertyNames in lib/js-instruments.ts (~74-86):
  // own property names plus every prototype's own names up the chain.
  let props = Object.getOwnPropertyNames(subject);
  let proto = Object.getPrototypeOf(subject);
  while (proto !== null) {
    props = props.concat(Object.getOwnPropertyNames(proto));
    proto = Object.getPrototypeOf(proto);
  }
  return props;
}

function isObject(object, propertyName) {
  // Mirror isObject in lib/js-instruments.ts (~418-430).
  let property;
  try {
    property = object[propertyName];
  } catch (e) {
    return false;
  }
  if (property === null) {
    return false;
  }
  return typeof property === "object";
}

function constructorName(obj) {
  try {
    return obj && obj.constructor ? obj.constructor.name : null;
  } catch (e) {
    return null;
  }
}

// The OWN property names of the prototype the stealth instrument resolves and
// hooks for a given constructor name, at depth 0. This MUST mirror the stealth
// resolution path exactly:
//   getContextualPrototypeFromString (Extension/src/stealth/instrument.ts ~477)
//     proto = window[ctor].prototype || Object.getPrototypeOf(window[ctor])
//   getPropertyNamesPerDepth(proto, 0) (instrument.ts ~427-444)
//     → Object.getOwnPropertyNames(proto)   // depth 0: ONLY the proto's OWN names
// Anything legacy's getPropertyNames(instance) covers beyond this set is an
// inherited-chain member the stealth depth-0 entry does NOT cover.
function stealthOwnNames(ctor) {
  if (!ctor) {
    return null;
  }
  let resolved;
  try {
    resolved = window[ctor];
  } catch (e) {
    return null;
  }
  if (!resolved) {
    return null;
  }
  let proto;
  try {
    proto = resolved.prototype ? resolved.prototype : Object.getPrototypeOf(resolved);
  } catch (e) {
    return null;
  }
  if (proto === undefined || proto === null) {
    return null;
  }
  try {
    return Object.getOwnPropertyNames(proto);
  } catch (e) {
    return null;
  }
}

// The universal prototypes every object inherits from. Members defined on these
// are, by default, surfaced as untranslated rather than emitted as a shared-prototype
// entry (instrumenting them would fire on virtually every receiver — site-wide
// flood / noise). This identity list is only a CONSERVATIVE in-realm hint: it
// reliably flags universal prototypes of objects created INSIDE the walker
// (content-script realm), but NOT those of page objects (e.g. ``navigator``),
// whose chain terminates in the PAGE realm's distinct ``Object.prototype`` — a
// different object that ``=== Object.prototype`` here does not match. The
// AUTHORITATIVE universal classification is therefore done by NAME on the Python
// side (``UNIVERSAL_PROTOTYPE_CONSTRUCTORS`` / ``is_universal``); this list only
// keeps content-script-realm universals out of the ``realInterface`` path.
function universalProtos() {
  const out = [];
  try { out.push(Object.prototype); } catch (e) {}
  try { out.push(Function.prototype); } catch (e) {}
  try { out.push(Array.prototype); } catch (e) {}
  return out;
}

// For a REACHED node, resolve where each INHERITED member is defined along the
// object's prototype chain: the owning prototype's interface name, and whether
// that prototype is a REAL global interface prototype (window[name].prototype)
// the stealth instrument can hook ONCE and attribute by receiver interface.
//
// Returns an array of {member, owner, realInterface} for every inherited member:
//   member        - the property name
//   owner         - constructor.name of the prototype object that owns it
//                   (e.g. "EventTarget" for addEventListener), or null
//   realInterface - true iff window[owner] && window[owner].prototype === proto
//                   (a hookable global interface prototype) AND proto is not an
//                   in-realm universal prototype (see universalProtos). NOTE: for
//                   a PAGE object reached through the Xray (e.g. navigator), even
//                   the universal owners (Object/Function/Array) report
//                   realInterface=true, because window[owner].prototype resolves
//                   the PAGE realm and matches the chain, while the content-script
//                   universalProtos identity list does not. Universal owners are
//                   thus disambiguated by NAME on the Python side
//                   (UNIVERSAL_PROTOTYPE_CONSTRUCTORS), not by this flag alone.
// "Inherited" = present in legacy's own+chain set but NOT an own name of the
// leaf interface's prototype (stealthOwnNames) — the exact gap the depth-0
// stealth entry misses.
function inheritedOwners(object, leafOwnSet) {
  const universals = universalProtos();
  // Null-prototype dedup map: a plain {} inherits toString/valueOf/... from
  // Object.prototype, so `name in seen` would spuriously match exactly the
  // Object.prototype members we are trying to record.
  const seen = Object.create(null);
  const out = [];
  let proto;
  try {
    proto = Object.getPrototypeOf(object);
  } catch (e) {
    return out;
  }
  // Skip the leaf interface's own prototype: its members are covered by the
  // depth-0 stealth entry and are not "inherited" for this purpose.
  while (proto !== null) {
    let ownerName = null;
    let ownerProto = proto;
    try {
      ownerName = proto.constructor ? proto.constructor.name : null;
    } catch (e) {
      ownerName = null;
    }
    // Conservative in-realm universal check: matches only when `proto` is the
    // SAME object as the content script's Object/Function/Array.prototype, i.e.
    // for objects created inside the walker. A page object's chain (e.g.
    // navigator) terminates in the PAGE realm's distinct Object.prototype, which
    // does NOT match here — so universal owners of page objects fall through as
    // realInterface=true and are disambiguated by NAME on the Python side
    // (UNIVERSAL_PROTOTYPE_CONSTRUCTORS). This check is not a robustness barrier
    // against page tampering; it is a best-effort filter for the in-realm case.
    let isUniversal = false;
    for (const u of universals) {
      if (u === proto) { isUniversal = true; break; }
    }
    let realInterface = false;
    if (!isUniversal && ownerName) {
      try {
        const g = window[ownerName];
        if (g && g.prototype === ownerProto) {
          realInterface = true;
        }
      } catch (e) {
        realInterface = false;
      }
    }
    let names;
    try {
      names = Object.getOwnPropertyNames(proto);
    } catch (e) {
      names = [];
    }
    for (const name of names) {
      if (leafOwnSet.indexOf(name) !== -1) {
        continue; // covered by the depth-0 stealth entry
      }
      if (name in seen) {
        continue; // first (closest) owner wins
      }
      seen[name] = true;
      // Interface-attributed shared-prototype capture targets shared METHODS:
      // the receiver-interface filter is applied at CALL time (logCall in
      // instrument.ts). Record whether the member is a plain function (data
      // property whose value is a function) so the sweep only attributes methods
      // to a shared-prototype entry; inherited accessors/data members take the
      // untranslated path (their call-time receiver cannot be filtered this way).
      let isFunction = false;
      try {
        const d = Object.getOwnPropertyDescriptor(proto, name);
        isFunction = !!(d && typeof d.value === "function");
      } catch (e) {
        isFunction = false;
      }
      out.push({
        member: name,
        owner: ownerName,
        realInterface: realInterface,
        isFunction: isFunction,
      });
    }
    try {
      proto = Object.getPrototypeOf(proto);
    } catch (e) {
      break;
    }
  }
  return out;
}

// One record per REACHED node, keyed by instrumentedName so a node is reported
// once even if several properties point at it.
const reached = {};

function recordNode(object, instrumentedName, propertyNames) {
  if (!(instrumentedName in reached)) {
    const ctor = constructorName(object);
    const leafOwn = stealthOwnNames(ctor);
    reached[instrumentedName] = {
      instrumentedName: instrumentedName,
      constructorName: ctor,
      // The names legacy instruments at this node: own + the ENTIRE prototype
      // chain (getPropertyNames), minus excluded — recorded in propertyNames.
      propertyNames: [],
      // The names the emitted stealth entry (object=ctor, depth 0) ACTUALLY
      // covers: the OWN names of window[ctor].prototype. null when the
      // constructor does not resolve to a hookable prototype.
      stealthOwnNames: leafOwn,
      // Per inherited member: which prototype owns it and whether that prototype
      // is a hookable global interface (→ interface-attributed shared-prototype
      // capture) or a universal prototype (→ untranslated). Keyed off the live chain.
      inheritedOwners: inheritedOwners(object, leafOwn || []),
    };
  }
  const seen = reached[instrumentedName].propertyNames;
  for (const p of propertyNames) {
    if (seen.indexOf(p) === -1) {
      seen.push(p);
    }
  }
}

// Faithful replay of instrumentObject (lib/js-instruments.ts ~660-732), recording
// instead of instrumenting.
function walk(object, instrumentedName, logSettings) {
  let propertiesToInstrument;
  if (logSettings.propertiesToInstrument === null) {
    propertiesToInstrument = [];
  } else if (logSettings.propertiesToInstrument.length === 0) {
    propertiesToInstrument = getPropertyNames(object);
  } else {
    propertiesToInstrument = logSettings.propertiesToInstrument;
  }

  const instrumentedHere = [];
  for (const propertyName of propertiesToInstrument) {
    if (logSettings.excludedProperties.indexOf(propertyName) !== -1) {
      continue;
    }
    if (
      logSettings.recursive &&
      logSettings.depth > 0 &&
      isObject(object, propertyName) &&
      propertyName !== "__proto__"
    ) {
      const newInstrumentedName = instrumentedName + "." + propertyName;
      const newLogSettings = Object.assign({}, logSettings);
      newLogSettings.depth = logSettings.depth - 1;
      newLogSettings.propertiesToInstrument = [];
      let child;
      try {
        child = object[propertyName];
      } catch (e) {
        child = undefined;
      }
      if (child !== undefined && child !== null) {
        walk(child, newInstrumentedName, newLogSettings);
      }
    }
    instrumentedHere.push(propertyName);
  }
  for (const propertyName of logSettings.nonExistingPropertiesToInstrument) {
    if (logSettings.excludedProperties.indexOf(propertyName) !== -1) {
      continue;
    }
    instrumentedHere.push(propertyName);
  }
  recordNode(object, instrumentedName, instrumentedHere);
}

const errors = [];
for (const setting of settings) {
  let object;
  try {
    // Mirror the legacy resolver: instrumentJS evals item.object
    // (lib/js-instruments.ts ~761).
    object = eval(setting.object);
  } catch (e) {
    errors.push({ object: setting.object, error: String(e) });
    continue;
  }
  if (object === undefined || object === null) {
    errors.push({ object: setting.object, error: "resolved to null/undefined" });
    continue;
  }
  walk(object, setting.instrumentedName, setting.logSettings);
}

return JSON.stringify({ reached: Object.values(reached), errors: errors });
