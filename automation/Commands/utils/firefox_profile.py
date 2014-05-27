### Code taken from KU Leuven collaboration ###
from glob import glob
import sqlite3
import time
import os

def tmp_sqlite_files_exist(path):
    """Check if temporary sqlite files(wal, shm) exist in a given path."""
    return glob(os.path.join(path, '*-wal')) or\
           glob(os.path.join(path, '*-shm'))


def sleep_until_sqlite_checkpoint(profile_dir, timeout=60):
    """We wait until all the shm and wal files are checkpointed to DB.

    https://www.sqlite.org/wal.html#ckpt.
    """
    while (timeout > 0 and tmp_sqlite_files_exist(profile_dir)):
        time.sleep(1)
        timeout -= 1
    print "Waited for %s seconds for sqlite checkpointing" % (60 - timeout)


def get_localStorage(profile_directory, mod_since):
    #TODO how to support modified since???
    ff_ls_file = os.path.join(profile_directory, 'webappsstore.sqlite')
    if not os.path.isfile(ff_ls_file):
        print "Cannot find localstorage DB %s" % ff_ls_file
    else:
        conn = sqlite3.connect(ff_ls_file)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT scope, KEY, value \
                    FROM webappsstore2 \
                    WHERE last;')
            rows =  cur.fetchall()
        return rows

def get_cookies(profile_directory, mod_since):
    cookie_db = os.path.join(profile_directory, 'cookies.sqlite')
    if not os.path.isfile(cookie_db):
        print "cannot find cookie.db", cookie_db
    else:
        conn = sqlite3.connect(cookie_db)
        with conn:
            c = conn.cursor()
            c.execute('SELECT baseDomain, name, value, host, path, expiry,\
                lastAccessed, creationTime, isSecure, isHttpOnly \
                FROM moz_cookies \
                WHERE lastAccessed > ?;',(int(mod_since*1000000),))
            rows = c.fetchall()
        return rows

if __name__=="__main__":
    import sqlite3
    loc = '~/Desktop/delete_this.sqlite'
    con = sqlite3.connect(os.path.expanduser(loc))
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS profile_cookies ( \
        id INTEGER PRIMARY KEY AUTOINCREMENT, \
        page_url VARCHAR(500) NOT NULL, \
        domain TEXT, \
        name TEXT, \
        value TEXT, \
        host TEXT, \
        path TEXT, \
        expiry INTEGER, \
        accessed INTEGER, \
        creationTime INTEGER,\
        isSecure INTEGER,\
        isHttpOnly INTEGER);")
    
    top_url = 'testing'
    rows = get_cookies('/home/sengleha/Desktop/alexa_10k_triton_1/', 0)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO profile_cookies (page_url, domain, name, value, \
                      host, path, expiry, accessed, creationTime, isSecure, isHttpOnly) \
                      VALUES (?,?,?,?,?,?,?,?,?,?,?)",(top_url,) + row)
            cur.execute(*query)
    con.commit()
    import ipdb; ipdb.set_trace()
