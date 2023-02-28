# import jsbeautifier
import plyvel
# import zlib

# SQLite


def fetchiter(cursor, arraysize=10000):
    """Generator for cursor results"""
    while True:
        rows = cursor.fetchmany(arraysize)
        if rows == []:
            break
        for row in rows:
            yield row


def list_placeholder(length, is_pg=False):
    """Returns a (?,?,?,?...) string of the desired length"""
    return '(' + '?,'*(length-1) + '?)'


def optimize_db(cursor):
    """Set options to make sqlite more efficient on a high memory machine"""
    cursor.execute("PRAGMA cache_size = -%i" % (0.1 * 10**7))  # 10 GB
    # Store temp tables, indicies in memory
    cursor.execute("PRAGMA temp_store = 2")


def build_index(cursor, column, tables):
    """Build an index on `column` for each table in `tables`"""
    if not type(tables) == list:
        tables = [tables]
    for table in tables:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS %s_%s_index ON "
            "%s(%s);" % (table, column, table, column)
        )


# Script content stored in LevelDB databases by content hash


def get_leveldb(db_path, compression='snappy'):
    """
    Returns an open handle for a leveldb database
    with proper configuration settings.
    """
    db = plyvel.DB(db_path,
                   lru_cache_size=10**9,
                   write_buffer_size=128*10**4,
                   bloom_filter_bits=128,
                   compression=compression)
    return db


def get_url_content(url, sqlite_cur, ldb_con, beautify=True, visit_id=None):
    """Return javascript content for given url.
    Parameters
    ----------
    url : string
        url to search content hash for
    sqlite_cur : sqlite3.Cursor
        cursor for crawl database
    ldb_con : plyvel.DB
        leveldb database storing javascript content
    beautify : boolean
        Control weather or not to beautify output
    visit_id : int
        (optional) `visit_id` of the page visit where this URL was loaded
    """
    return get_url_content_with_hash(
        url, sqlite_cur, ldb_con, beautify, visit_id)[1]


def get_url_content_with_hash(url, sqlite_cur, ldb_con,
                              beautify=True, visit_id=None):
    """Return javascript content for given url.
    Parameters
    ----------
    url : string
        url to search content hash for
    sqlite_cur : sqlite3.Cursor
        cursor for crawl database
    ldb_con : plyvel.DB
        leveldb database storing javascript content
    beautify : boolean
        Control weather or not to beautify output
    visit_id : int
        (optional) `visit_id` of the page visit where this URL was loaded
    """
    if visit_id is not None:
        sqlite_cur.execute(
            "SELECT content_hash FROM http_responses WHERE "
            "visit_id = ? AND url = ? LIMIT 1;", (visit_id, url))
    else:
        sqlite_cur.execute(
            "SELECT content_hash FROM http_responses WHERE url = ? LIMIT 1;",
            (url,))
    content_hash = sqlite_cur.fetchone()
    if (content_hash is None
            or len(content_hash) == 0
            or content_hash[0] is None):
        return
    content_hash = content_hash[0]
    content = get_content(ldb_con, content_hash, beautify=beautify)
    if content is None:
        return
    return (content_hash, content)


def get_channel_content(visit_id, channel_id,
                        sqlite_cur, ldb_con, beautify=True):
    """Return javascript content for given channel_id.
    Parameters
    ----------
    visit_id : int
        `visit_id` of the page visit where this URL was loaded
    channel_id : string
        `channel_id` to search content hash for
    sqlite_cur : sqlite3.Cursor
        cursor for crawl database
    ldb_con : plyvel.DB
        leveldb database storing javascript content
    beautify : boolean
        Control weather or not to beautify output
    """
    return get_channel_content_with_hash(
        visit_id, channel_id, sqlite_cur, ldb_con, beautify)[1]


def get_channel_content_with_hash(visit_id, channel_id,
                                  sqlite_cur, ldb_con, beautify=True):
    """Return javascript content for given channel_id.
    Parameters
    ----------
    visit_id : int
        `visit_id` of the page visit where this URL was loaded
    channel_id : string
        `channel_id` to search content hash for
    sqlite_cur : sqlite3.Cursor
        cursor for crawl database
    ldb_con : plyvel.DB
        leveldb database storing javascript content
    beautify : boolean
        Control weather or not to beautify output
    """
    sqlite_cur.execute(
        "SELECT content_hash FROM http_responses "
        "WHERE channel_id = ? AND visit_id = ? LIMIT 1;",
        (channel_id, visit_id)
    )
    content_hash = sqlite_cur.fetchone()
    if (content_hash is None
            or len(content_hash) == 0
            or content_hash[0] is None):
        return
    content_hash = content_hash[0]
    content = get_content(ldb_con, content_hash, beautify=beautify)
    if content is None:
        return
    return (content_hash, content)


def get_content(db, content_hash, compression='snappy', beautify=True):
    """ Returns decompressed content from javascript leveldb database """
    if content_hash is None:
        print("ERROR: content_hash can't be None...")
        return
    content = db.get(str(content_hash))
    if content is None:
        print("ERROR: content hash: %s NOT FOUND" % content_hash)
        return
    supported = ['snappy', 'none', 'gzip']
    if compression not in supported:
        print("Unsupported compression type %s. Only %s "
              "are the supported options." % (compression, str(supported)))
        return
    elif compression == 'gzip':
        try:
            content = zlib.decompress(content, zlib.MAX_WBITS | 16)
        except Exception:
            try:
                content = zlib.decompress(content)
            except Exception:
                print("Failed to decompress gzipped content...")
                return
    if beautify:
        return jsbeautifier.beautify(content)
    else:
        return content
