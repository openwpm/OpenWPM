/**
 * This enables us to keep information about the original order
 * in which events arrived to our event listeners.
 */
let eventOrdinal = 0;

export const incrementedEventOrdinal = () => {
  return eventOrdinal++;
};
