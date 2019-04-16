#!/bin/bash
set -e

cd automation/Extension/firefox
npm install
npm run build
cp dist/*.zip ./openwpm.xpi
