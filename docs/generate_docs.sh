#!/bin/bash

sphinx-apidoc -f -o source ../automation
sphinx-build -M html . _build