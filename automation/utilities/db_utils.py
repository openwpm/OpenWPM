
import os
import sqlite3

import plyvel

CONTENT_DB_NAME = 'content.ldb'


def query_db(db, query, params=None, as_tuple=False):
    """Run a query against the given db.

    If params is not None, securely construct a query from the given
    query string and params.
    """
    with sqlite3.connect(db) as con:
        if not as_tuple:
            con.row_factory = sqlite3.Row
        if params is None:
            rows = con.execute(query).fetchall()
        else:
            rows = con.execute(query, params).fetchall()
    return rows


def get_content(data_directory):
    """Yield key, value pairs from the deduplicated leveldb content database

    Parameters
    ----------
    data_directory : string
        root directory of the crawl files containing the content database
    """
    db_path = os.path.join(data_directory, CONTENT_DB_NAME)
    db = plyvel.DB(db_path,
                   create_if_missing=False,
                   compression='snappy')
    for content_hash, content in db.iterator():
        yield content_hash, content
    db.close()


def get_javascript_entries(db, all_columns=False, as_tuple=False):
    if all_columns:
        select_columns = "*"
    else:
        select_columns = "script_url, symbol, operation, value, arguments"

    return query_db(db, "SELECT %s FROM javascript" % select_columns,
                    as_tuple=as_tuple)


def any_command_failed(db):
    """Returns True if any command in a given database failed"""
    rows = query_db(db, "SELECT * FROM crawl_history;")
    for row in rows:
        if row['command_status'] != 'ok':
            return True
    return False
