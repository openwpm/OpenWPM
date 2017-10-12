from __future__ import absolute_import
from __future__ import print_function

from collections import OrderedDict
from copy import deepcopy
import json
import os
import six
import subprocess

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


def ensure_firefox_in_path():
    """
    If ../../firefox-bin/ exists, add it to the PATH.
    If firefox-bin does not exist, we throw a RuntimeError.
    """
    root_dir = os.path.dirname(__file__)  # directory of this file
    ffbin = os.path.abspath(root_dir + "/../../firefox-bin")
    if os.path.isdir(ffbin):
        curpath = os.environ["PATH"]
        if ffbin not in curpath:
            os.environ["PATH"] = ffbin + os.pathsep + curpath
    else:
        raise RuntimeError(
            "The `firefox-bin` directory is not found in the root of the "
            "OpenWPM directory. Did you run the install script "
            "(`install.sh`)?")


def get_version():
    """Return OpenWPM version tag/current commit and Firefox version """
    try:
        openwpm = subprocess.check_output(
            ["git", "describe", "--tags", "--always"]).strip()
    except subprocess.CalledProcessError:
        ver = os.path.join(os.path.dirname(__file__), '../../VERSION')
        with open(ver, 'r') as f:
            openwpm = f.readline().strip()

    ensure_firefox_in_path()
    try:
        firefox = subprocess.check_output(["firefox", "--version"])
    except subprocess.CalledProcessError as e:
        six.raise_from(
            RuntimeError("Firefox not found.  Did you run `./install.sh`?"),
            e)

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
