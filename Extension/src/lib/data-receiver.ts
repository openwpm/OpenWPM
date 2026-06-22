/**
 * Shared shape of the object instruments use to persist records and content.
 *
 * In production this is the `loggingdb` module namespace; the instruments only
 * ever touch `saveRecord` / `saveContent`, so this narrow interface is enough
 * to type their constructors without coupling to the full module.
 */
export interface DataReceiver {
  saveRecord(instrument: string, record: object): void;
  saveContent(content: string | Uint8Array, contentHash: string): Promise<void>;
  logInfo(msg: string): void;
  logDebug(msg: string): void;
  logWarn(msg: string): void;
  logError(msg: string): void;
  logCritical(msg: string): void;
}
