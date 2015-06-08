from ..MPLogger import loggingclient
import MITMProxy

from libmproxy import proxy
from libmproxy.proxy.server import ProxyServer
import threading
import socket
import Queue
import os


def init_proxy(db_socket_address, logger_address, crawl_id):
    """
    # deploys an (optional) instance of mitmproxy used to log crawl data
    <db_socket_address> is the connection address of the DataAggregator
    <crawl_id> is the id set by the TaskManager
    """
    logger = loggingclient(*logger_address)
    proxy_site_queue = Queue.Queue()  # queue for crawler to communicate with proxy

    # gets local port from one of the free ports
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    proxy_port = sock.getsockname()[1]
    sock.close()


    config = proxy.ProxyConfig(cadir=os.path.join(os.path.dirname(__file__), 'cert'),port=proxy_port)
    server = ProxyServer(config)
    logger.info('BROWSER %i: Intercepting Proxy listening on %i' % (crawl_id, proxy_port))
    m = MITMProxy.InterceptingMaster(server, crawl_id, proxy_site_queue, db_socket_address, logger_address)
    thread = threading.Thread(target=m.run, args=())
    thread.daemon = True
    thread.start()
    return proxy_port, proxy_site_queue
