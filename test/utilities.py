from publicsuffix import PublicSuffixList, fetch
import SimpleHTTPServer
import SocketServer
import threading
import codecs
import os
import sqlite3
from random import choice
LOCAL_WEBSERVER_PORT = 8000
PSL_CACHE_LOC = '/tmp/public_suffix_list.dat'
BASE_TEST_URL_DOMAIN = "localtest.me"
BASE_TEST_URL_NOPATH = "http://%s:%s" % (BASE_TEST_URL_DOMAIN,
                                         LOCAL_WEBSERVER_PORT)
BASE_TEST_URL = "%s/test_pages" % BASE_TEST_URL_NOPATH

class MyTCPServer(SocketServer.TCPServer):
    """Subclass TCPServer to be able to reuse the same port (Errno 98)."""
    allow_reuse_address = True


def start_server():
    """ Start a simple HTTP server to run local tests.

    We need this since page-mod events in the extension
    don't fire on `file://*`. Instead, point test code to
    `http://localtest.me:8000/test_pages/...`
    """
    print "Starting HTTP Server in a separate thread"
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    server = MyTCPServer(("localhost", LOCAL_WEBSERVER_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print "...serving at port", LOCAL_WEBSERVER_PORT
    return server, thread


def rand_str(size=8):
    """Return random string with the given size."""
    RAND_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join(choice(RAND_CHARS) for _ in range(size))


def get_psl():
    """
    Grabs an updated public suffix list.
    """
    if not os.path.isfile(PSL_CACHE_LOC):
        print "%s does not exist, downloading a copy." % PSL_CACHE_LOC
        psl_file = fetch()
        with codecs.open(PSL_CACHE_LOC, 'w', encoding='utf8') as f:
            f.write(psl_file.read())
    psl_cache = codecs.open(PSL_CACHE_LOC, encoding='utf8')
    return PublicSuffixList(psl_cache)


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


def get_javascript_entries(db, all_columns=False):
    if all_columns:
        select_columns = "*"
    else:
        select_columns = "script_url, symbol, operation, value, parameter_index,\
             parameter_value"

    return query_db(db, "SELECT %s FROM javascript" % select_columns)
