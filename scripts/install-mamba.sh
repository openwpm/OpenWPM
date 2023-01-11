#!/bin/bash

# This script installs mamba.
# It is only intended for use by travis and docker container

# Users/Developers should install mamba themselves
# via the instructions at https://mamba.readthedocs.io/en/latest/installation.html
# Mamba has been chosen as a replacement for conda as it performs much faster
# and consumes less resources

# Ref: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/use-conda-with-travis-ci.html
wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh" -O mamba.sh;
bash mamba.sh -b -p $HOME/mamba
source "$HOME/mamba/etc/profile.d/conda.sh"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
