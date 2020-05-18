#!/bin/bash

# This script re-creates environment.yaml
# This script will remove an existing openwpm
# conda environment if it exists.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"

# Create openwpm env with unpinned yaml file
conda env create --force -q -f environment-unpinned.yaml

# Activate
conda activate openwpm

# Adding dev dependencies to environment
conda env update -f environment-unpinned-dev.yaml

# Export the environment including manually specify channels
conda env export --no-builds --override-channels -c conda-forge -c main -f ../environment.yaml

# Prune environment file to only things we want to pin
python prune-environment.py

echo 'New environment.yaml successfully created.'
