### This is code adapted from KU Leuven crawler code written by
### Gunes Acar and Marc Juarez

from __future__ import absolute_import
from __future__ import print_function

import fnmatch
import os
import six
import sys
import traceback

from miniamf import sol

#TODO: Linux only
FLASH_DIRS = ['~/.macromedia/Flash_Player/#SharedObjects/']

class FlashCookie(object):
    filename = ''
    domain = ''
    local_path = ''
    key = ''
    content = ''

def gen_find_files(filepat, top):
    """
    http://www.dabeaz.com/generators/
    returns filenames that matches the given pattern under() a given dir
    """
    for path, _, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, filepat):
            yield os.path.join(path, name)

def get_flash_cookies(mod_since=0):
    """Return a list of Flash cookies (Local Shared Objects)."""
    flash_cookies = list()
    for top_dir in FLASH_DIRS:
        top_dir = os.path.expanduser(top_dir)
        for lso_file in gen_find_files("*.sol", top_dir):
            mtime = os.path.getmtime(lso_file)
            if mtime > mod_since:
                try:
                    flash_cookies.extend(parse_flash_cookies(lso_file))
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    sys.stderr.write("Exception reading {!r}:\n"
                                     .format(lso_file))
                    traceback.print_exc()

    return flash_cookies

def parse_flash_cookies(lso_file):
    lso_dict = sol.load(lso_file)
    flash_cookies = list()
    for k, v in six.iteritems(lso_dict):
        flash_cookie = FlashCookie()
        flash_cookie.local_path = lso_file.split("#SharedObjects/")[1]
        flash_cookie.filename = os.path.basename(lso_file)
        flash_cookie.domain = lso_file.split("#SharedObjects/")[1].split("/")[1]
        if not isinstance(k, six.text_type):
            flash_cookie.key = six.text_type(k, errors='backslashreplace')
        if not isinstance(v, six.text_type):
            flash_cookie.content = six.text_type(v, errors='backslashreplace')

        flash_cookies.append(flash_cookie)
    return flash_cookies
