#!/bin/bash
set -e

wget https://fpdownload.adobe.com/get/flashplayer/pdc/32.0.0.223/flash_player_npapi_linux.x86_64.tar.gz
tar -xzvf flash_player_npapi_linux.x86_64.tar.gz libflashplayer.so
mv libflashplayer.so firefox-bin/
rm flash_player_npapi_linux.x86_64.tar.gz
