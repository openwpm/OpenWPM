#!/bin/bash

# Use cached durations if available, fall back to committed baseline
if [ -f .test_durations_cached ]; then
    DURATIONS_PATH=.test_durations_cached
else
    DURATIONS_PATH=.test_durations
fi

if [ -n "$GROUP" ] && [ -n "$SPLITS" ]; then
    # CI mode: use pytest-split for optimal distribution
    python -m pytest --splits "$SPLITS" --group "$GROUP" \
        --splitting-algorithm least_duration \
        --durations-path "$DURATIONS_PATH" \
        --cov=openwpm --junit-xml=junit-report.xml --cov-report=xml \
        -s -v --durations=10
else
    # Local mode: run specific tests or all
    python -m pytest --cov=openwpm --junit-xml=junit-report.xml \
        --cov-report=xml $TESTS -s -v --durations=10
fi
