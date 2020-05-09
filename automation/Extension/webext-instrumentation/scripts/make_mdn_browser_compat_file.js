const bcd = require('mdn-browser-compat-data');
const fs = require('fs')

const BROWSER = 'firefox'
const VERSION = 75

const output = `
// This file is generated from mdn-browser-compat-data....AASADFA.
const api = [
    'XMLHttpRequest'
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

    console.log("The file was saved!");
});