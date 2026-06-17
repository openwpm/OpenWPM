/**
 * Realm entry point of the stealth instrument.
 *
 * Bundled to ``privileged/stealthInstrument/realm.js`` and loaded by
 * ``OpenWPMStealthChild.sys.mjs`` into a sandbox created for one window global,
 * with that window as prototype, Xrays and export helpers: the shape of a
 * content-script sandbox, so module state (record ordinal, record cap) is per
 * realm.
 */

import { setHost } from "./host";
import { startInstrument } from "./instrument";
import { JSInstrumentSettings } from "../types/js_instrument_settings";

// Defined on the sandbox by the actor child before this script is loaded.
declare const openwpmSend: (type: string, payload: string) => void;
declare const openwpmSettings: string;
declare const openwpmPin: (original: unknown) => unknown;
declare const openwpmIsPinnerError: (error: unknown) => boolean;
declare const openwpmIsProxy: (value: object) => boolean;

function parseSettings(): JSInstrumentSettings | undefined {
  if (typeof openwpmSettings !== "string" || !openwpmSettings) {
    return undefined;
  }
  try {
    return JSON.parse(openwpmSettings);
  } catch (error) {
    console.error("OpenWPM: unparseable stealth settings", error);
    return undefined;
  }
}

const settings = parseSettings();

setHost({
  send(type: string, data: any) {
    let payload: string;
    try {
      payload = JSON.stringify(data);
    } catch (error) {
      console.error("OpenWPM: unserialisable stealth record", error);
      return;
    }
    openwpmSend(type, payload);
  },
  pinNative: (original: unknown) => openwpmPin(original),
  isPinnerError: (error: unknown) => openwpmIsPinnerError(error),
  isProxy: (value: object) => openwpmIsProxy(value),
  exportFunction: (func: any, targetScope: any, options: any) =>
    (globalThis as any).exportFunction(func, targetScope, options),
  settings: () => settings,
  // The instrument's own frames come from resource://openwpm/.
  ownFramePrefixes: () => ["moz-extension://", "resource://openwpm/"],
});

try {
  startInstrument((globalThis as any).window);
} catch (error) {
  console.error(
    "OpenWPM: stealth instrumentation failed",
    error,
    (error as Error)?.stack,
  );
}
