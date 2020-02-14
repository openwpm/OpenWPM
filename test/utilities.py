
import os
import socketserver
import threading
from http.server import SimpleHTTPRequestHandler
from os.path import dirname, realpath
from random import choice
from urllib.parse import parse_qs, urlparse

import boto3
import pyarrow.parquet as pq
import s3fs
from botocore.credentials import Credentials
from pyarrow.filesystem import S3FSWrapper  # noqa

LOCAL_WEBSERVER_PORT = 8000
BASE_TEST_URL_DOMAIN = "localtest.me"
BASE_TEST_URL_NOPATH = "http://%s:%s" % (BASE_TEST_URL_DOMAIN,
                                         LOCAL_WEBSERVER_PORT)
BASE_TEST_URL = "%s/test_pages" % BASE_TEST_URL_NOPATH
BASE_TEST_URL_NOSCHEME = BASE_TEST_URL.split('//')[1]


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


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
        if self.path.startswith('/MAGIC_REDIRECT/'):
            parsed_path = urlparse(self.path)
            qs = parse_qs(parsed_path.query)
            if 'dst' not in qs:
                self.send_error(
                    404,
                    "Requests to the path `/MAGIC_REDIRECT/` must specify "
                    "a destination to redirect to via a `dst` query parameter."
                )
                return
            dst = qs['dst'][0]
            new_qs = list()
            if len(qs['dst']) > 1:
                new_qs.append('dst=' + '&dst='.join(qs['dst'][1:]))
            for key in qs.keys():
                if key == 'dst':
                    continue
                temp = '%s=' + '&%s='.join(qs[key])
                new_qs.append(temp % key)
            if len(new_qs) > 0:
                new_url = "%s?%s" % (dst, '&'.join(new_qs))
            else:
                new_url = dst
            self.send_response(301)
            self.send_header("Location", new_url)
            self.end_headers()
            return

        # Otherwise, return file from disk
        return SimpleHTTPRequestHandler.do_GET(self, *args, **kwargs)


def start_server():
    """ Start a simple HTTP server to run local tests.

    We need this since page-mod events in the extension
    don't fire on `file://*`. Instead, point test code to
    `http://localtest.me:8000/test_pages/...`
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


def rand_str(size=8):
    """Return random string with the given size."""
    RAND_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join(choice(RAND_CHARS) for _ in range(size))


class LocalS3Session(object):
    """
    Ensures that the local s3 service is used when
    setup as the default boto3 Session
    Based on localstack_client/session.py
    """

    def __init__(self, aws_access_key_id='accesskey',
                 aws_secret_access_key='secretkey',
                 aws_session_token='token', region_name='us-east-1',
                 endpoint_url='http://localhost:4572',
                 botocore_session=None, profile_name=None,
                 localstack_host=None):
        self.env = 'local'
        self.session = boto3.session.Session()
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.region_name = region_name
        self.endpoint_url = endpoint_url

    def resource(self, service_name, **kwargs):
        return self.session.resource(
            service_name,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name, verify=False
        )

    def get_credentials(self):
        return Credentials(
            access_key=self.aws_access_key_id,
            secret_key=self.aws_secret_access_key,
            token=self.aws_session_token
        )

    def client(self, service_name, **kwargs):
        return self.session.client(
            service_name, endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name, verify=False
        )


def local_s3_bucket(resource, name='localstack-foo'):
    bucket = resource.Bucket(name)
    bucket.create()
    return name


class LocalS3Dataset(object):
    def __init__(self, bucket, directory):
        self.bucket = bucket
        self.root_directory = directory
        self.visits_uri = '%s/%s/visits/%%s' % (
            self.bucket, self.root_directory)
        self.s3_fs = s3fs.S3FileSystem(session=LocalS3Session())
        boto3.DEFAULT_SESSION = LocalS3Session()
        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')

    def load_table(self, table_name):
        return pq.ParquetDataset(
            self.visits_uri % table_name,
            filesystem=self.s3_fs
        ).read_pandas().to_pandas()

    def list_files(self, directory, prepend_root=False):
        bucket = self.s3_resource.Bucket(self.bucket)
        files = list()
        if prepend_root:
            prefix = "%s/%s/" % (self.root_directory, directory)
        else:
            prefix = directory
        for summary in bucket.objects.filter(Prefix=prefix):
            files.append(summary.key)
        return files

    def get_file(self, filename, prepend_root=False):
        if prepend_root:
            key = "%s/%s" % (self.root_directory, filename)
        else:
            key = filename
        obj = self.s3_client.get_object(
            Bucket=self.bucket,
            Key=key
        )
        body = obj["Body"]
        content = body.read()
        body.close()
        return content
