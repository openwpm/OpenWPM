#!/bin/sh
export PYTHONNOUSERSITE=$(cat "${BASH_SOURCE%/*}/"../old_python_user_site)