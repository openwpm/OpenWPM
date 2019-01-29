#!/bin/bash
set -e

rm -rf automation/Extension/firefox
git clone https://github.com/nhnt11/openwpm-firefox-webext automation/Extension/firefox
cd automation/Extension/firefox
npm install
npm run build
cp dist/*.zip ./openwpm.xpi
