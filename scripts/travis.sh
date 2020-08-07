#!/bin/bash
if [[ "$TESTS" == "webextension" ]]; then
    cd automation/Extension/webext-instrumentation;
    npm test;
else
    cd test;
    if ! python -m pytest --cov=../automation --cov-report=xml $TESTS -s -v --durations=10; then
        exit $?;
    fi
    codecov -f coverage.xml;
fi