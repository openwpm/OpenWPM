#!/usr/bin/env python
# Usage: TESTS=0 python scripts/ci.py scripts/distribution.json
import json
import os
import subprocess
from sys import argv

test_selection = os.getenv("TESTS")
assert len(argv) == 2
if test_selection is None:
    print("Please set TESTS environment variable")
    exit(1)
with open(argv[1]) as f:
    test_distribution = json.load(f)
if test_selection == "other":
    res = subprocess.run("pytest --collect-only -q", capture_output=True, shell=True)
    res.check_returncode()
    actual_tests = res.stdout.decode("utf-8").splitlines()
    for index, test in enumerate(actual_tests):
        if len(test) == 0:  # cut off warnings
            actual_tests = actual_tests[:index]

    all_known_tests = set(sum(test_distribution, []))
    actual_tests_set = set(actual_tests)
    known_but_dont_exist = all_known_tests.difference(actual_tests_set)
    exist_but_arent_known = actual_tests_set.difference(all_known_tests)
    if len(known_but_dont_exist) > 0 or len(exist_but_arent_known) > 0:
        print("known_but_dont_exist:", known_but_dont_exist)
        print("exist_but_arent_known", exist_but_arent_known)
        print("Uncovered or outdated tests")
        exit(2)
else:
    index = int(test_selection)
    tests = " ".join('"' + test + '"' for test in test_distribution[index])
    subprocess.run(
        "pytest "
        "--cov=openwpm --junit-xml=junit-report.xml "
        f"--cov-report=xml {tests} "
        "-s -v --durations=10;",
        shell=True,
        check=True,
    )
    subprocess.run("codecov -f coverage.xml", shell=True, check=True)
