import os
import socketserver
import threading
from http.server import SimpleHTTPRequestHandler
from os.path import dirname, realpath
from urllib.parse import parse_qs, urlparse

LOCAL_WEBSERVER_PORT = 8000
BASE_TEST_URL_DOMAIN = "localhost"
BASE_TEST_URL_NOPATH = "http://%s:%s" % (BASE_TEST_URL_DOMAIN, LOCAL_WEBSERVER_PORT)
BASE_TEST_URL = "%s/test_pages" % BASE_TEST_URL_NOPATH
BASE_TEST_URL_NOSCHEME = BASE_TEST_URL.split("//")[1]


class MyTCPServer(socketserver.TCPServer):
    """Subclass TCPServer to be able to reuse the same port (Errno 98)."""

    allow_reuse_address = True


class MyHandler(SimpleHTTPRequestHandler):
    """Subclass SimpleHTTPRequestHandler to support custom responses.
    Supported custom responses:

    1. Magic path to that responds with 301 redirects.
    Any request that starts with `/MAGIC_REDIRECT/` will respond with a
    redirect to the path given in the `dst` query string parameter of the
    request URL. All other query strings parameters are preserved.

    If multiple `dst` query string parameters are specified, the
    first parameter value is used and the remaining are appended to the new
    location. E.g.:

    A request to `/MAGIC_REDIRECT/image1.gif?
                  dst=/MAGIC_REDIRECT/image2.gif&
                  dst=/MAGIC_REDIRECT/image3.gif&
                  dst=/shared/test_image.png`
    will lead to the following requests:
        1. `/MAGIC_REDIRECT/image1.gif?
                dst=/MAGIC_REDIRECT/image2.gif&
                dst=/MAGIC_REDIRECT/image3.gif&
                dst=/shared/test_image.png`
        2. `/MAGIC_REDIRECT/image2.gif?
                dst=/MAGIC_REDIRECT/image3.gif&
                dst=/shared/test_image.png`
        3. `/MAGIC_REDIRECT/image3.gif?&dst=/shared/test_image.png`
        4. `/shared/test_image.png`

    If a request is made the to `/MAGIC_REDIRECT/` path without a
    `dst` parameter defined, a `404` response is returned.
    """

    def __init__(self, *args, **kwargs):
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_GET(self, *args, **kwargs):

        # 1. Redirect all requests to `/MAGIC_REDIRECT/`.
        if self.path.startswith("/MAGIC_REDIRECT/"):
            parsed_path = urlparse(self.path)
            qs = parse_qs(parsed_path.query)
            if "dst" not in qs:
                self.send_error(
                    404,
                    "Requests to the path `/MAGIC_REDIRECT/` must specify "
                    "a destination to redirect to via a `dst` query parameter.",
                )
                return
            dst = qs["dst"][0]
            new_qs = list()
            if len(qs["dst"]) > 1:
                new_qs.append("dst=" + "&dst=".join(qs["dst"][1:]))
            for key in qs.keys():
                if key == "dst":
                    continue
                temp = "%s=" + "&%s=".join(qs[key])
                new_qs.append(temp % key)
            if len(new_qs) > 0:
                new_url = "%s?%s" % (dst, "&".join(new_qs))
            else:
                new_url = dst
            self.send_response(301)
            self.send_header("Location", new_url)
            self.end_headers()
            return

        # Otherwise, return file from disk
        return SimpleHTTPRequestHandler.do_GET(self, *args, **kwargs)


def start_server():
    """Start a simple HTTP server to run local tests.

    We need this since page-mod events in the extension
    don't fire on `file://*`. Instead, point test code to
    `http://localhost:8000/test_pages/...`
    """
    print("Starting HTTP Server in a separate thread")
    # switch to test dir, this is where the test files are
    os.chdir(dirname(realpath(__file__)))
    server = MyTCPServer(("0.0.0.0", LOCAL_WEBSERVER_PORT), MyHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print("...serving at port", LOCAL_WEBSERVER_PORT)
    return server, thread
