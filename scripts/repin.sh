#!/bin/bash

# This script re-creates environment.yaml
# This script will remove an existing openwpm
# conda environment if it exists.

set -e

# Make conda available to shell script
eval "$(conda shell.bash hook)"

# Create openwpm env with unpinned yaml file
# `PYTHONNOUSERSITE` set so python ignores local user site libraries when building the env
# See: https://github.com/openwpm/OpenWPM/pull/682#issuecomment-645648939
case "$(uname -s)" in
Darwin)
  echo 'Using the osx-64 channel for MacOS dependencies...'
  CONDA_SUBDIR=osx-64 PYTHONNOUSERSITE=True conda env create --yes -q -f environment-unpinned.yaml
  ;;
*)
  PYTHONNOUSERSITE=True conda env create --yes -q -f environment-unpinned.yaml
  ;;
esac

# Activate
conda activate openwpm

# Adding dev dependencies to environment
case "$(uname -s)" in
Darwin)
  echo 'Using the osx-64 channel for MacOS dependencies...'
  CONDA_SUBDIR=osx-64 PYTHONNOUSERSITE=True conda env update -f environment-unpinned-dev.yaml
  ;;
*)
  PYTHONNOUSERSITE=True conda env update -f environment-unpinned-dev.yaml
  ;;
esac


# Export the environment including manually specify channels
conda env export --no-builds --override-channels -c conda-forge -f ../environment.yaml

# Prune environment file to only things we want to pin
python manage-environment.py prune

echo 'New environment.yaml successfully created.'
