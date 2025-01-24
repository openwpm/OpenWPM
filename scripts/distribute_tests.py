#!/usr/bin/env python
# Usage: python scripts/distribute_tests.py junit-report.xml 7 scripts/distribution.json
# Where junit-report.xml is the result of running
# python -m pytest --cov=openwpm --junit-xml=junit-report.xml --cov-report=xml test/ -s -v --durations=10
import json
from sys import argv
from typing import Any
from xml.etree import ElementTree as ET

assert len(argv) == 4

num_runner = int(argv[2])
tree = ET.parse(argv[1])
root = tree.getroot()
testcases: list[dict[str, Any]] = []
for testcase in root.iter("testcase"):
    # Build correct test name based on naming convention
    classname = testcase.get("classname")
    assert isinstance(classname, str)
    split = classname.rsplit(".", 1)
    if split[1][0].isupper():  # Test is in a class
        split[0] = split[0].replace(".", "/")
        split[0] = split[0] + ".py"
        path = split[0] + "::" + split[1]
    else:
        path = classname.replace(".", "/") + ".py"
    time = testcase.get("time")
    assert isinstance(time, str)
    testcases.append({"path": f'{path}::{testcase.get("name")}', "time": float(time)})

sorted_testcases = sorted(testcases, key=lambda x: x["time"], reverse=True)
total_time = sum(k["time"] + 0.5 for k in sorted_testcases)
time_per_runner = total_time / num_runner
print(f"Total time: {total_time} Total time per runner: {total_time / num_runner}")
distributed_testcases: list[list[str]] = [[] for _ in range(num_runner)]
estimated_time = []
for subsection in distributed_testcases:
    time_spent = 0
    tmp = []
    for testcase in sorted_testcases:
        if time_spent + testcase["time"] < time_per_runner:
            tmp.append(testcase)
            time_spent += testcase["time"] + 0.5  # account for overhead per testcase
    for testcase in tmp:
        sorted_testcases.remove(testcase)
    subsection[:] = [testcase["path"] for testcase in tmp]
    estimated_time.append(time_spent)

assert len(sorted_testcases) == 0, print(len(sorted_testcases))
print(estimated_time)
with open(argv[3], "w") as f:
    json.dump(distributed_testcases, f, indent=0)
