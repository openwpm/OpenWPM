/**
 * Parent side of the webdriver-spoof actor.
 *
 * All the work happens in the child, in the content process. This side exists
 * because a JSWindowActor is registered as a pair; it carries no logic.
 */
export class OpenWPMWebdriverSpoofParent extends JSWindowActorParent {}
