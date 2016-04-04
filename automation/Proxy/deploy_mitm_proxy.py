from ..MPLogger import loggingclient
import MITMProxy

from libmproxy import proxy
from libmproxy.proxy.server import ProxyServer
import threading
import socket
import Queue
import os


def init_proxy(browser_params, manager_params, status_queue):
    """
    Uses mitmproxy used to log HTTP Requests and Responses
    <browser params> configuration parameters of host browser
    <manager_params> configuration parameters of the TaskManager
    <status_queue> a Queue to report proxy status back to TaskManager
    """
    logger = loggingclient(*manager_params['logger_address'])
    proxy_site_queue = Queue.Queue()  # queue for crawler to communicate with proxy

    # gets local port from one of the free ports
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    proxy_port = sock.getsockname()[1]
    sock.close()

    config = proxy.ProxyConfig(cadir=os.path.join(os.path.dirname(__file__), 'cert'),port=proxy_port)
    server = ProxyServer(config)
    logger.info('BROWSER %i: Intercepting Proxy listening on %i' % (browser_params['crawl_id'], proxy_port))
    m = MITMProxy.InterceptingMaster(server, proxy_site_queue, browser_params, manager_params, status_queue)
    thread = threading.Thread(target=m.run, args=())
    thread.daemon = True
    thread.start()
    return proxy_port, proxy_site_queue
