import os
import socketserver
import threading
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler
from os.path import dirname, realpath
from urllib.parse import parse_qs, urlparse

BASE_TEST_URL_DOMAIN = "localhost"


@dataclass(frozen=True)
class ServerUrls:
    """URLs for the test HTTP server, computed from the dynamic port."""

    port: int
    domain: str = BASE_TEST_URL_DOMAIN

    @property
    def base_nopath(self) -> str:
        return f"http://{self.domain}:{self.port}"

    @property
    def base(self) -> str:
        return f"{self.base_nopath}/test_pages"

    @property
    def base_noscheme(self) -> str:
        return self.base.split("//")[1]

    def url(self, path: str) -> str:
        return self.base + path


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

    def send_response(self, code, message=None):
        self._response_code = code
        super().send_response(code, message)

    def end_headers(self):
        if getattr(self, "_response_code", None) == 200:
            self.send_header("Cache-Control", "max-age=3600")
        super().end_headers()

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


def start_server() -> tuple[MyTCPServer, threading.Thread, ServerUrls]:
    """Start a simple HTTP server to run local tests.

    We need this since page-mod events in the extension
    don't fire on `file://*`. Instead, point test code to
    `http://localhost:<port>/test_pages/...`

    Binds to port 0 (OS-assigned free port) to allow parallel test runs.
    """
    print("Starting HTTP Server in a separate thread")
    # switch to test dir, this is where the test files are
    os.chdir(dirname(realpath(__file__)))
    server = MyTCPServer(("0.0.0.0", 0), MyHandler)
    port = server.server_address[1]
    urls = ServerUrls(port=port)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print("...serving at port", port)
    return server, thread, urls
