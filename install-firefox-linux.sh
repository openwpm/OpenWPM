#!/bin/bash
set -e

# Use the Unbranded build that corresponds to Firefox 68 release (source: https://wiki.mozilla.org/Add-ons/Extension_Signing#Unbranded_Builds)
wget https://queue.taskcluster.net/v1/task/HYGMEM_UT06yMsOpWtHyVQ/runs/0/artifacts/public/build/target.tar.bz2
tar jxf target.tar.bz2
rm -rf firefox-bin
mv firefox firefox-bin
rm target.tar.bz2
