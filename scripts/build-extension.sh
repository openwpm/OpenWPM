#!/bin/bash
set -e

cd automation/Extension/firefox
npm install
npm run build
cp dist/*.zip ./openwpm.xpi

echo "Success: automation/Extension/firefox/openwpm.xpi has been built"
