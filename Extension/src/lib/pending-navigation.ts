import { Navigation } from "../schema";

/**
 * Ties together the two separate navigation events that together holds information about both parent frame id and transition-related attributes
 */
export class PendingNavigation {
  public readonly onBeforeNavigateEventNavigation: Promise<Navigation>;
  public readonly onCommittedEventNavigation: Promise<Navigation>;
  public resolveOnBeforeNavigateEventNavigation: (details: Navigation) => void;
  public resolveOnCommittedEventNavigation: (details: Navigation) => void;
  constructor() {
    this.onBeforeNavigateEventNavigation = new Promise((resolve) => {
      this.resolveOnBeforeNavigateEventNavigation = resolve;
    });
    this.onCommittedEventNavigation = new Promise((resolve) => {
      this.resolveOnCommittedEventNavigation = resolve;
    });
  }
  public resolved() {
    return Promise.all([
      this.onBeforeNavigateEventNavigation,
      this.onCommittedEventNavigation,
    ]);
  }

  /**
   * Either returns or times out and returns undefined or
   * returns the results from resolved() above
   *
   * @param ms
   */
  public async resolvedWithinTimeout(ms) {
    const resolved = await Promise.race([
      this.resolved(),
      new Promise((resolve) => setTimeout(resolve, ms)),
    ]);
    return resolved;
  }
}
