#!/bin/bash
if [[ "$TESTS" == "webextension" ]]; then
    cd openwpm/Extension/webext-instrumentation;
    npm test;
else
    cd test;
    python -m pytest --cov=../openwpm --cov-report=xml $TESTS -s -v --durations=10;
    exit_code=$?;
    if [[ "$exit_code" -ne 0 ]]; then
        exit $exit_code;
    fi
    codecov -f coverage.xml;
fi
