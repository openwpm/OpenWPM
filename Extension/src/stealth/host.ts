/**
 * What ``instrument.ts`` and ``error.ts`` need from the realm sandbox they run
 * in, bound by ``actor.ts``.
 */

import { JSInstrumentSettings } from "../types/js_instrument_settings";

export interface StealthHost {
  /** Deliver one instrumentation record to the collector. */
  send(type: string, data: any): void;

  /**
   * ``Function.prototype.call`` bound to the page native ``original``, owned by
   * a compartment whose wrappers survive the native's window.
   */
  pinNative(original: unknown): unknown;

  /** Whether ``error`` was created in the realm ``pinNative`` calls from. */
  isPinnerError(error: unknown): boolean;

  /** Whether a page object is a scripted Proxy, without running its traps. */
  isProxy(value: object): boolean;

  /** The sandbox's ``exportFunction``. */
  exportFunction(func: any, targetScope: any, options: any): any;

  /** The study's instrumentation surface, if it configured one. */
  settings(): JSInstrumentSettings | undefined;

  /**
   * URL prefixes of stack frames that belong to the instrument or another
   * extension, never shown to or recorded from a page.
   */
  ownFramePrefixes(): string[];
}

let host: StealthHost | undefined;

export function setHost(newHost: StealthHost): void {
  host = newHost;
}

export function getHost(): StealthHost {
  if (!host) {
    throw new Error("OpenWPM stealth: no host binding installed");
  }
  return host;
}

/**
 * True when ``frame`` (``name@location:line:col``) originates from the
 * instrument rather than the page. Own frames carry exactly one ``@``, followed
 * by an own prefix: a page controls its function names and script URLs, and
 * can put ``@`` and an extension scheme in either.
 */
export function isOwnFrame(frame: string): boolean {
  const at = frame.indexOf("@");
  if (at === -1 || frame.includes("@", at + 1)) {
    return false;
  }
  const location = frame.slice(at + 1);
  return getHost()
    .ownFramePrefixes()
    .some((prefix) => location.startsWith(prefix));
}
