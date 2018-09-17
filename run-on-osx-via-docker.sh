#!/usr/bin/env bash

# This script facilitate starting a shell / running tests
# within the Docker environment on Mac OSX
#
# Usage: ./run-on-osx-via-docker.sh <optional-command-to-run>
#
# If <optional-command-to-run> is left out, an interactive
# shell within the Docker environment is initiated

export IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
xhost + $IP
export DISPLAY=$IP:0
docker run \
    -v $PWD/docker-volume:/home/user/ \
    -v $PWD:/opt/OpenWPM/ \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    -it openwpm-dev $@
