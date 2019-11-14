#!/bin/sh
pgrep python | xargs -n 1 kill
while [[pgrep python ]]
do
    sleep(100)
done
echo "Successfully shut down"