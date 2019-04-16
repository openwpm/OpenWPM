# This is code adapted from KU Leuven crawler code written by
# Gunes Acar and Marc Juarez
from __future__ import absolute_import, print_function

import os
import sqlite3
import time
from glob import glob
from shutil import copy2


def tmp_sqlite_files_exist(path):
    """Check if temporary sqlite files(wal, shm) exist in a given path."""
    return glob(os.path.join(path, '*-wal')) or \
        glob(os.path.join(path, '*-shm'))


def sleep_until_sqlite_checkpoint(profile_dir, timeout=60):
    """
    We wait until all the shm and wal files are checkpointed to DB.
    https://www.sqlite.org/wal.html#ckpt.
    """
    while (timeout > 0 and tmp_sqlite_files_exist(profile_dir)):
        time.sleep(1)
        timeout -= 1
    print("Waited for %s seconds for sqlite checkpointing" % (60 - timeout))


def get_localStorage(profile_directory, mod_since):
    # TODO how to support modified since???
    ff_ls_file = os.path.join(profile_directory, 'webappsstore.sqlite')
    if not os.path.isfile(ff_ls_file):
        print("Cannot find localstorage DB %s" % ff_ls_file)
    else:
        conn = sqlite3.connect(ff_ls_file)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT scope, KEY, value \
                    FROM webappsstore2 \
                    WHERE last;')
            rows = cur.fetchall()
        return rows


def get_cookies(profile_directory, mod_since):
    cookie_db = os.path.join(profile_directory, 'cookies.sqlite')
    if not os.path.isfile(cookie_db):
        print("cannot find cookie.db", cookie_db)
    else:
        cookie_db_copy = os.path.join(profile_directory, 'cookies_copy.sqlite')
        copy2(cookie_db, cookie_db_copy)
        conn = sqlite3.connect(cookie_db_copy)
        conn.row_factory = sqlite3.Row
        with conn:
            c = conn.cursor()
            c.execute('SELECT baseDomain, name, value, host, path, expiry,\
                lastAccessed, creationTime, isSecure, isHttpOnly \
                FROM moz_cookies \
                WHERE lastAccessed > ? ; ', (int(mod_since * 1000000),))
            rows = c.fetchall()
        os.remove(cookie_db_copy)
        return rows
