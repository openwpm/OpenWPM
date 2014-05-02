### This is code adapted from KU Leuven crawler code ###
from pyamf import sol
import file_utils as fu
import os

FLASH_DIRS = ['~/.macromedia/Flash_Player/#SharedObjects/']

class FlashCookie(object):
    filename = ''
    domain = ''
    local_path = ''
    key = ''
    content = ''

def get_flash_cookies(mod_since=0):
    """Return a list of Flash cookies (Local Shared Objects)."""
    flash_cookies = list()
    for top_dir in FLASH_DIRS:
        top_dir = os.path.expanduser(top_dir)
        for lso_file in fu.gen_find_files("*.sol", top_dir):
            mtime = os.path.getmtime(lso_file)
            print "lso_file = " + lso_file
            print "mtime = " + str(mtime) + " | mod_since = " + str(mod_since)
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

if __name__=="__main__":
    import sqlite3
    loc = '~/Desktop/delete_this.sqlite'
    con = sqlite3.connect(os.path.expanduser(loc))
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS flash_cookies (\
            id INTEGER PRIMARY KEY AUTOINCREMENT,\
            page_url VARCHAR(500) NOT NULL,\
            domain VARCHAR(500),\
            filename VARCHAR(500),\
            local_path VARCHAR(1000),\
            key TEXT,\
            content TEXT);")
    
    top_url = 'testing'
    flash_cookies = get_flash_cookies()
    for cookie in flash_cookies:
        query = ("INSERT INTO flash_cookies (page_url, domain, filename, local_path, \
                  key, content) VALUES (?,?,?,?,?,?)", 
                  (top_url, cookie.domain, cookie.filename, cookie.local_path, 
                  cookie.key, cookie.content))
        cur.execute(*query)
    con.commit()
    import ipdb; ipdb.set_trace()
