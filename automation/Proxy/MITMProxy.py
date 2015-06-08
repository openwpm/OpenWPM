from ..SocketInterface import clientsocket
from ..MPLogger import loggingclient
import mitm_commands

from libmproxy import controller
import Queue
import sys


class InterceptingMaster (controller.Master):
    """
    Customized MITMProxy
    Extends the proxy controller to add some additional
    functionality for handling /logging requests and responses

    Inspired by the following example. Note the gist has a lot of bugs.
    https://gist.github.com/dannvix/5285924
    """
    
    def __init__(self, server, crawl_id, url_queue, db_socket_address, logger_address):
        self.crawl_id = crawl_id
        
        # Attributes used to flag the first-party domain
        self.url_queue = url_queue  # first-party domain provided by BrowserManager
        self.prev_top_url, self.curr_top_url = None, None  # previous and current top level domains
        self.prev_requests, self.curr_requests = set(), set()  # set of requests for previous and current site

        # Open a socket to communicate with DataAggregator
        self.db_socket = clientsocket()
        self.db_socket.connect(*db_socket_address)

        # Open a socket to communicate with MPLogger
        self.logger = loggingclient(*logger_address)

        controller.Master.__init__(self, server)

    def load_process_message(self, q, timeout):
        """ Tries to read and process a message from the proxy queue, returns True iff this succeeds """
        try:
            msg = q.get(timeout=timeout)
            controller.Master.handle(self, *msg)
            return True
        except Queue.Empty:
            return False

    def tick(self, q, timeout=0.01):
        """ new tick function used to label first-party domains and avoid race conditions when doing so """
        if self.curr_top_url is None:  # proxy is fresh, need to get first-party domain right away
            self.curr_top_url = self.url_queue.get()
        elif not self.url_queue.empty():  # new FP has been visited
            # drains the queue to get rid of stale messages from previous site
            while self.load_process_message(q, timeout):
                pass

            self.prev_requests, self.curr_requests = self.curr_requests, set()
            self.prev_top_url, self.curr_top_url = self.curr_top_url, self.url_queue.get()

        self.load_process_message(q, timeout)

    def run(self):
        """ Light wrapper around run with error printing """
        try:
            controller.Master.run(self)
        except KeyboardInterrupt:
            print 'KeyboardInterrupt received. Shutting down'
            self.shutdown()
            sys.exit(0)
        except Exception as ex:
            self.logger.critical('BROWSER %i: Exception. Shutting down proxy!\n%s' % (self.crawl_id, str(ex)))
            self.shutdown()
            raise

    def handle_request(self, msg):
        """ Receives HTTP request, and sends it to logging function """
        msg.reply()
        self.curr_requests.add(msg.request)
        mitm_commands.process_general_mitm_request(self.db_socket, self.crawl_id, self.curr_top_url, msg)

    # Record data from HTTP responses
    def handle_response(self, msg):
        """ Receives HTTP response, and sends it to logging function """
        msg.reply()

        # attempts to get the top url, based on the request object
        if msg.request in self.prev_requests:
            top_url = self.prev_top_url
            self.prev_requests.remove(msg.request)
        elif msg.request in self.curr_requests:
            top_url = self.curr_top_url
            self.curr_requests.remove(msg.request)
        else:  # ignore responses for which we cannot match the request
            return

        mitm_commands.process_general_mitm_response(self.db_socket, self.crawl_id, top_url, msg)
