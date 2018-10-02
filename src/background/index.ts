import * as cookieInstrument from './cookie-instrument.js';
import * as jsInstrument from './javascript-instrument.js';
import * as httpInstrument from './http-instrument.js';

export const background = { cookieInstrument, jsInstrument, httpInstrument };
