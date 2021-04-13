import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any, AnyStr, Iterator, List, Tuple, Union

import plyvel


def query_db(
    db: Path, query: str, params: Iterable = None, as_tuple: bool = False
) -> List[Union[sqlite3.Row, Tuple[Any, ...]]]:
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


def get_content(db_name: Path) -> Iterator[Tuple[AnyStr, AnyStr]]:
    """Yield key, value pairs from the deduplicated leveldb content database

    Parameters
    ----------
    db_name : Path
        The full path to the current db
    """
    db = plyvel.DB(str(db_name), create_if_missing=False, compression="snappy")
    for content_hash, content in db.iterator():
        yield content_hash, content
    db.close()


def get_javascript_entries(
    db: Path, all_columns: bool = False, as_tuple: bool = False
) -> List[Union[Tuple[Any, ...], sqlite3.Row]]:
    if all_columns:
        select_columns = "*"
    else:
        select_columns = "script_url, symbol, operation, value, arguments"

    return query_db(db, f"SELECT {select_columns} FROM javascript", as_tuple=as_tuple)


def any_command_failed(db: Path) -> bool:
    """Returns True if any command in a given database failed"""
    rows = query_db(db, "SELECT * FROM crawl_history;")
    for row in rows:
        assert isinstance(row, sqlite3.Row)
        if row["command_status"] != "ok":
            return True
    return False
