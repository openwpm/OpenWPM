const bcd = require('mdn-browser-compat-data');
const fs = require('fs')

const BROWSER = 'firefox'
const VERSION = 75

const api = [];
Object.keys(bcd.api).forEach(item => {
    if (item !== '__compat') {
        api.push(`"${item}"`);
    }
});

const output = `
# This file is generated from mdn-browser-compat-data by running
# "npm run make-compat" in the Extension/webext-instrumentation
# directory.
api = [
  ${api.join(',\n  ')}
]`
fs.writeFile(
    '../../js_instrumentation/mdn-browser-compat-data.py',
    output,
    (err) => {
    if(err) {
        return console.log(err);
    }
    console.log("../../js_instrumentation/mdn-browser-compat-data.py regenerated.");
});