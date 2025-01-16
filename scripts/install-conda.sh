#!/bin/bash

# This script installs conda.
# It is only intended for use by travis and docker container

# Users/Developers should install conda themselves
# via the instructions at https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html

# Ref: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/use-conda-with-travis-ci.html
wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -O conda.sh;
bash conda.sh -b -p $HOME/conda
source "$HOME/conda/etc/profile.d/conda.sh"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
