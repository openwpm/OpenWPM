#!/bin/bash

sphinx-apidoc -f -o source ../openwpm
sphinx-build -M html . _build