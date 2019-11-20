# This is code adapted from KU Leuven crawler code written by
# Gunes Acar and Marc Juarez


import fnmatch
import os
import sys
import traceback
from collections import namedtuple

from miniamf import sol


def ensure_unicode(val):
    """Coerce VAL to a Unicode string by any means necessary."""
    if isinstance(val, str):
        return val
    if not isinstance(val, bytes):
        return str(val)
    try:
        return val.decode("utf-8", "backslashescape")
    except (UnicodeDecodeError, TypeError):
        # Backslash escaping on decode doesn't work in Python 2.
        # This does approximately the same thing.
        return (val.decode("latin1")
                .encode("ascii", "backslashreplace")
                .decode("ascii"))

# TODO: Linux only


FLASH_DIRS = ['~/.macromedia/Flash_Player/#SharedObjects/']


_BaseFlashCookie = namedtuple(
    '_BaseFlashCookie',
    ('filename', 'domain', 'local_path', 'key', 'content'))


class FlashCookie(_BaseFlashCookie):
    def __new__(self, path, key, content):
        local_path = path.split("#SharedObjects/")[1]
        filename = os.path.basename(path)
        domain = local_path.split("/")[1]
        key = ensure_unicode(key)
        content = ensure_unicode(content)

        return _BaseFlashCookie.__new__(
            self, filename, domain, local_path, key, content)


def parse_flash_cookies(lso_file):
    lso_dict = sol.load(lso_file)
    return [FlashCookie(lso_file, k, v) for k, v in iter(lso_dict.items())]


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
                except Exception:
                    sys.stderr.write("Exception reading {!r}:\n"
                                     .format(lso_file))
                    traceback.print_exc()

    return flash_cookies
