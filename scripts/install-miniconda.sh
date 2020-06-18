#!/bin/bash

# This script installs miniconda.
# It is only intended for use by travis and docker container

# Users/Developers should install miniconda themselves
# via the instructions at https://docs.conda.io/en/latest/miniconda.html
# Miniconda is not required if a user already has anaconda on their
# system as anaconda comes with conda.

# Ref: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/use-conda-with-travis-ci.html
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
bash miniconda.sh -b -p $HOME/miniconda
source "$HOME/miniconda/etc/profile.d/conda.sh"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
