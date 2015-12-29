from publicsuffix import PublicSuffixList, fetch
import SimpleHTTPServer
import SocketServer
import threading
import codecs
import os

PSL_CACHE_LOC = '/tmp/public_suffix_list.dat'

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

def start_server():
    """ Start a simple http server to run local tests
    
    We need this since page-mod events in the extension 
    don't fire on `file://*`. Instead, point test code to
    `http://localhost:8000/test_pages/...`
    """
    print "Starting HTTP Server in a separate thread"
    PORT = 8000
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    server = SocketServer.TCPServer(("localhost", PORT), Handler)
    thread = threading.Thread(target = server.serve_forever)
    thread.daemon = True
    thread.start()
    print "...serving at port", PORT
    return server, thread
