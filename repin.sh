#!/bin/bash

# This script re-creates environment.yaml
# This script will remove an existing openwpm
# conda environment if it exists.

case "$(uname -s)" in
  Darwin)
    ENV_SUFFIX='-macosx'
    ;;
  Linux)
    ENV_SUFFIX=''
    ;;
  *)
    echo 'Your OS is not supported. Aborting'
    exit 1
    ;;
esac

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"

# Create openwpm env with unpinned yaml file
conda env create --force -q -f environment-unpinned.yaml

# Adding dev dependencies to environment
conda env update -n openwpm -f environment-unpinned-dev.yaml

# Export the environment including manually specify channels
conda env export -n openwpm --no-builds --override-channels -c conda-forge -c main -f environment$ENV_SUFFIX.yaml

# Remove prefix line from end of export (it doesn't actually
# have an impact, but it's confusing so this gives us a cleaner
# environment.yaml)
sed -i '$d' environment.yaml

echo 'New environment.yaml successfully created.'
