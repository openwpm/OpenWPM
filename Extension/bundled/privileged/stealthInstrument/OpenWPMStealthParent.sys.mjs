/**
 * Parent side of the stealth-instrument actor.
 *
 * All the work happens in the child, in the content process, and records go
 * straight to the parent process over the process message manager. This side
 * exists because a JSWindowActor is registered as a pair; it carries no logic.
 */
export class OpenWPMStealthParent extends JSWindowActorParent {}
