#!/bin/bash
if [[ "$TESTS" == "webextension" ]]; then
    cd automation/Extension/webext-instrumentation;
    npm test;
else
    cd test;
    python -m pytest --cov=../automation --cov-report=xml $TESTS -s -v --durations=10;
    exit_code=$?;
    if [[ "$exit_code" -ne 0 ]]; then
        exit $exit_code;
    fi
    codecov -f coverage.xml;
fi
