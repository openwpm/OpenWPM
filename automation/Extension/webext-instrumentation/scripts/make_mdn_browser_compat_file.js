const bcd = require('mdn-browser-compat-data');
const fs = require('fs')

const BROWSER = 'firefox'
const VERSION = 75

const api = [];
Object.keys(bcd.api).forEach(item => {
    try {
        let version_added = bcd.api[item].__compat.support.firefox.version_added;
        if ( ( version_added !== null ) && ( version_added <= VERSION ) ) {
            api.push(`"${item}"`);
        }
    } catch(error) {
        console.log(error);
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
    '../../../docs/mdn_browser_compat_data.py',
    output,
    (err) => {
    if(err) {
        return console.log(err);
    }
    console.log("../../../docs/mdn_browser_compat_data.py regenerated.");
});