#!/bin/bash
set -e

# Check if we're running on continuous integration
# Python requirements are already installed by .travis.yml on Travis
if [ "$TRAVIS" != "true" ]; then
  wget https://bootstrap.pypa.io/get-pip.py
  python get-pip.py --user
  export PATH=~/.local/bin:$PATH
  rm get-pip.py
	pip install --user --upgrade -r requirements.txt
fi
