#!/bin/sh
set -o errexit
pgrep python | xargs -n 1 kill
echo "Test"
while true
do
  pgrep python > /dev/null;
  x=$?
  echo "$x was the last status"
  if [ $x -eq 0 ]; then
    wait 100
  else
    break
  fi
done
echo "Successfully shut down"
