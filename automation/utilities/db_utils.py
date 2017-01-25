import sqlite3
import os
import plyvel


def query_db(db, query, params=None):
    """Run a query against the given db.

    If params is not None, securely construct a query from the given
    query string and params.
    """
    with sqlite3.connect(db) as con:
        if params is None:
            rows = con.execute(query).fetchall()
        else:
            rows = con.execute(query, params).fetchall()
    return rows


def get_javascript_content(data_directory):
    """Yield key, value pairs from the deduplicated leveldb content database

    Parameters
    ----------
    data_directory : str
        root directory of the crawl files containing `javascript.ldb`
    """
    db_path = os.path.join(data_directory, 'javascript.ldb')
    db = plyvel.DB(db_path,
                   create_if_missing=False,
                   compression='snappy')
    for content_hash, content in db.iterator():
        yield content_hash, content
    db.close()


def get_javascript_entries(db, all_columns=False):
    if all_columns:
        select_columns = "*"
    else:
        select_columns = "script_url, symbol, operation, value, arguments"

    return query_db(db, "SELECT %s FROM javascript" % select_columns)


def any_command_failed(db):
    """Returns True if any command in a given database failed"""
    rows = query_db(db, "SELECT * FROM CrawlHistory;")
    for row in rows:
        if row[3] != 1:
            return True
    return False
