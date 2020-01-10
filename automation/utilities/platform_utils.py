
import json
import os
import subprocess
from collections import OrderedDict
from copy import deepcopy
from sys import platform

from tabulate import tabulate


def parse_http_stack_trace_str(trace_str):
    """Parse a stacktrace string and return an array of dict."""
    stack_trace = []
    frames = trace_str.split("\n")
    for frame in frames:
        try:
            func_name, rest = frame.split("@", 1)
            rest, async_cause = rest.rsplit(";", 1)
            filename, line_no, col_no = rest.rsplit(":", 2)
            stack_trace.append({
                               "func_name": func_name,
                               "filename": filename,
                               "line_no": line_no,
                               "col_no": col_no,
                               "async_cause": async_cause,
                               })
        except Exception as exc:
            print("Exception parsing the stack frame %s %s" % (frame, exc))
    return stack_trace


def get_firefox_binary_path():
    """
    If ../../firefox-bin/firefox-bin or os.environ["FIREFOX_BINARY"] exists,
    return it. Else, throw a RuntimeError.
    """
    if "FIREFOX_BINARY" in os.environ:
        firefox_binary_path = os.environ["FIREFOX_BINARY"]
        if not os.path.isfile(firefox_binary_path):
            raise RuntimeError(
                "No file found at the path specified in "
                "environment variable `FIREFOX_BINARY`."
                "Current `FIREFOX_BINARY`: %s" % firefox_binary_path)
        return firefox_binary_path

    root_dir = os.path.dirname(__file__) + "/../.."
    if platform == 'darwin':
        firefox_binary_path = os.path.abspath(
            root_dir + "/Nightly.app/Contents/MacOS/firefox-bin")
    else:
        firefox_binary_path = os.path.abspath(
            root_dir + "/firefox-bin/firefox-bin")

    if not os.path.isfile(firefox_binary_path):
        raise RuntimeError(
            "The `firefox-bin/firefox-bin` binary is not found in the root "
            "of the  OpenWPM directory (did you run the install script "
            "(`install.sh`)?). Alternatively, you can specify a binary "
            "location using the OS environment variable FIREFOX_BINARY.")
    return firefox_binary_path


def get_geckodriver_exec_path():
    """
    If the geckodriver executable does not exist next to the Firefox binary,
    we throw a RuntimeError.
    """
    firefox_binary_path = get_firefox_binary_path()
    geckodriver_executable_path = (
        os.path.dirname(firefox_binary_path) + "/geckodriver")

    if not os.path.isfile(geckodriver_executable_path):
        raise RuntimeError(
            "The `geckodriver` executable is not found next to the "
            "Firefox binary. Did you run the install script (`install.sh`)?")
    return geckodriver_executable_path


def get_version():
    """Return OpenWPM version tag/current commit and Firefox version """
    try:
        openwpm = subprocess.check_output(
            ["git", "describe", "--tags", "--always"]).strip()
    except subprocess.CalledProcessError:
        ver = os.path.join(os.path.dirname(__file__), '../../VERSION')
        with open(ver, 'r') as f:
            openwpm = f.readline().strip()

    firefox_binary_path = get_firefox_binary_path()
    try:
        firefox = subprocess.check_output([firefox_binary_path, "--version"])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Firefox not found. "
                           " Did you run `./install.sh`?") from e

    ff = firefox.split()[-1]
    return openwpm, ff


def get_configuration_string(manager_params, browser_params, versions):
    """Construct a well-formatted string for {manager,browser}params

    Constructs a pretty printed string of all parameters. The config
    dictionaries are split to try to avoid line wrapping for reasonably
    size terminal windows.
    """

    config_str = "\n\nOpenWPM Version: %s\nFirefox Version: %s\n" % versions
    config_str += "\n========== Manager Configuration ==========\n"
    config_str += json.dumps(manager_params, sort_keys=True,
                             indent=2, separators=(',', ': '))
    config_str += "\n\n========== Browser Configuration ==========\n"
    print_params = [deepcopy(x) for x in browser_params]
    table_input = list()
    profile_dirs = OrderedDict()
    archive_dirs = OrderedDict()
    profile_all_none = archive_all_none = True
    for item in print_params:
        crawl_id = item['crawl_id']

        # Update print flags
        if item['profile_tar'] is not None:
            profile_all_none = False
        if item['profile_archive_dir'] is not None:
            archive_all_none = False

        # Separate out long profile directory strings
        profile_dirs[crawl_id] = item.pop('profile_tar')
        archive_dirs[crawl_id] = item.pop('profile_archive_dir')

        # Copy items in sorted order
        dct = OrderedDict()
        dct[u'crawl_id'] = crawl_id
        for key in sorted(item.keys()):
            dct[key] = item[key]
        table_input.append(dct)

    key_dict = OrderedDict()
    counter = 0
    for key in table_input[0].keys():
        key_dict[key] = counter
        counter += 1
    config_str += "Keys:\n"
    config_str += json.dumps(key_dict, indent=2,
                             separators=(',', ': '))
    config_str += '\n\n'
    config_str += tabulate(table_input, headers=key_dict)

    config_str += "\n\n========== Input profile tar files ==========\n"
    if profile_all_none:
        config_str += "  No profile tar files specified"
    else:
        config_str += json.dumps(profile_dirs, indent=2,
                                 separators=(',', ': '))

    config_str += "\n\n========== Output (archive) profile dirs ==========\n"
    if archive_all_none:
        config_str += "  No profile archive directories specified"
    else:
        config_str += json.dumps(archive_dirs, indent=2,
                                 separators=(',', ': '))

    config_str += '\n\n'
    return config_str
