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
// This file is generated from mdn-browser-compat-data by running
// "npm run make-compat"
const api = [
  ${api.join(',\n  ')}
];
export {api};
`
fs.writeFile(
    'src/lib/mdn-browser-compat-data.ts',
    output,
    (err) => {
    if(err) {
        return console.log(err);
    }
    console.log("src/lib/mdn-browser-compat-data.ts regenerated.");
});