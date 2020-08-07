#!/bin/sh
echo $PYTHONNOUSERSITE > "${BASH_SOURCE%/*}/"../old_python_user_site
export PYTHONNOUSERSITE=True
