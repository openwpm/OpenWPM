### This is code adapted from KU Leuven crawler code written by
### Gunes Acar and Marc Juarez
from pyamf import sol
import fnmatch
import os

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
                except Exception as e:
                    print "Exception reading", lso_file
                    print e
                    pass
    return flash_cookies

def parse_flash_cookies(lso_file):
    lso_dict = sol.load(lso_file)
    flash_cookies = list()
    for k, v in lso_dict.iteritems():
        flash_cookie = FlashCookie()
        flash_cookie.local_path = lso_file.split("#SharedObjects/")[1]
        flash_cookie.filename = os.path.basename(lso_file)
        flash_cookie.domain = lso_file.split("#SharedObjects/")[1].split("/")[1]
        flash_cookie.key = unicode(k)
        try:
            flash_cookie.content = unicode(v)
        except UnicodeDecodeError:
            # obj is byte string
            ascii_text = str(v).encode('string_escape')
            flash_cookie.content = unicode(ascii_text)

        flash_cookies.append(flash_cookie)
    return flash_cookies
