#!/usr/bin/env bash

# This script facilitate starting a shell / running tests
# within the Docker environment on Mac OSX
#
# Usage: ./run-on-osx-via-docker.sh <optional-command-to-run>
#
# If <optional-command-to-run> is left out, an interactive
# shell within the Docker environment is initiated

# remove artifacts from locally run tests if any (or else
# we will run into a ImportMismatchError)
rm -rf .pytest_cache/
rm -rf test/__pycache__/

# Allow access to XQuartz for the current IP
export IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
xhost + $IP
export DISPLAY=$IP:0

# start the docker environment with X server forwarding
if [ "$#" == 0 ]; then
    echo "Starting a shell in the Docker environment"
else
    echo "Running '$@' in the Docker environment"
fi
docker run \
    -v $PWD/docker-volume:/home/user/Desktop/ \
    -v $PWD:/opt/OpenWPM/ \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --shm-size=2g \
    -it openwpm $@
