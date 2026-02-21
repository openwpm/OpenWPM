#!/bin/bash

python -m pytest --cov=openwpm --junit-xml=junit-report.xml --cov-report=xml $TESTS -s -v --durations=10;
