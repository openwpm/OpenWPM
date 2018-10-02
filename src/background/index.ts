import * as cookieInstrument from './cookie-instrument';
import * as jsInstrument from './javascript-instrument';
import * as httpInstrument from './http-instrument';

export const background = { cookieInstrument, jsInstrument, httpInstrument };
