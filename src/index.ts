import { CookieInstrument } from "./background/cookie-instrument";
import { HttpInstrument } from "./background/http-instrument";
import { JavascriptInstrument } from "./background/javascript-instrument";

const background = { CookieInstrument, JavascriptInstrument, HttpInstrument };

import { JavascriptInstrumentContentScope } from "./content/javascript-instrument-content-scope";

const content = { JavascriptInstrumentContentScope };

import * as HttpPostParser from "./lib/http-post-parser";

const lib = { HttpPostParser };

export { background, content, lib };
