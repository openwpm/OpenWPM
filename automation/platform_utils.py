from collections import OrderedDict
from tabulate import tabulate
from copy import deepcopy
import subprocess
import json
import os

def get_version():
    """Return OpenWPM version tag/current commit and Firefox version """
    openwpm = subprocess.check_output(["git","describe","--tags"]).strip()

    ff_ini = os.path.join(os.path.dirname(__file__), '../firefox-bin/application.ini')
    with open(ff_ini, 'r') as f:
        ff = None
        for line in f:
            if line.startswith('Version='):
                ff = line[8:].strip()
                break
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
    ext_settings = list()
    table_input = list()
    profile_dirs = OrderedDict()
    archive_dirs = OrderedDict()
    extension_all_disabled = profile_all_none = archive_all_none = True
    for item in print_params:
        crawl_id = item['crawl_id']

        # Update print flags
        if item['profile_tar'] is not None:
            profile_all_none = False
        if item['profile_archive_dir'] is not None:
            archive_all_none = False
        if item['extension']['enabled']:
            extension_all_disabled = False

        # Separate out extension settings
        dct = OrderedDict()
        dct['crawl_id'] = crawl_id
        dct.update(item.pop('extension'))
        ext_settings.append(dct)

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

    config_str += "\n\n========== Extension Configuration ==========\n"
    if extension_all_disabled:
        config_str += "  No extensions enabled"
    else:
        config_str += tabulate(ext_settings, headers="keys")

    config_str += "\n\n========== Input profile tar files ==========\n"
    if profile_all_none:
        config_str += "  No profile tar files specified"
    else:
        config_str += json.dumps(profile_dirs, indent=2,
                                 separators=(',', ': '))

    config_str += "\n\n========== Output (archive) profile directories ==========\n"
    if archive_all_none:
        config_str += "  No profile archive directories specified"
    else:
        config_str += json.dumps(archive_dirs, indent=2,
                                 separators=(',', ': '))

    config_str += '\n\n'
    return config_str
