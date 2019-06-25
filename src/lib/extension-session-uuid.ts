import { makeUUID } from "./uuid";

/**
 * This enables us to access a unique reference to this browser
 * session - regenerated any time the background process gets
 * restarted (which should only be on browser restarts)
 */
export const extensionSessionUuid = makeUUID();
