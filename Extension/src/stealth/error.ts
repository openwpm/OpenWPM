import { isOwnFrame } from "./host";

/*
 * Provides the index the first call outside of the extension
 */
function getBeginOfScriptCalls(lines: string[]) {
  for (let i = 0; i < lines.length; i++) {
    if (!isOwnFrame(lines[i])) {
      return i;
    }
  }
  return -1;
}

/*
 * Drops the instrument's own frames, and any extension's, from a stack-trace
 * frame array, leaving only page frames. Used to keep the recorded call_stack
 * free of them even when the page calls back into instrumented APIs (which
 * interleaves them mid-stack).
 */
function filterExtensionFrames(frames: string[]): string[] {
  return frames.filter((frame) => !isOwnFrame(frame));
}

// Helper to get originating script urls
function getStackTrace() {
  let stack;

  try {
    throw new Error();
  } catch (err) {
    stack = (err as any).stack;
  }

  return stack;
}

export { filterExtensionFrames, getBeginOfScriptCalls, getStackTrace };
