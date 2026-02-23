#!/bin/bash

if [ -n "$GROUP" ] && [ -n "$SPLITS" ]; then
    # CI mode: use pytest-split for optimal distribution
    python -m pytest --splits "$SPLITS" --group "$GROUP" --splitting-algorithm least_duration --cov=openwpm --junit-xml=junit-report.xml --cov-report=xml -s -v --durations=10
else
    # Local mode: run specific tests or all
    python -m pytest --cov=openwpm --junit-xml=junit-report.xml --cov-report=xml $TESTS -s -v --durations=10
fi
