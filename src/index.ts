import * as cookieInstrument from "./background/cookie-instrument";
import * as httpInstrument from "./background/http-instrument";
import * as jsInstrument from "./background/javascript-instrument";

const background = { cookieInstrument, jsInstrument, httpInstrument };

import * as jsInstrumentContentScope from "./content/javascript-instrument-content-scope";

const content = { jsInstrumentContentScope };

import * as HttpPostParser from "./lib/http-post-parser";

const lib = { HttpPostParser };

export { background, content, lib };
