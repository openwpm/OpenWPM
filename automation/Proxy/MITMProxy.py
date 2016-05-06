from ..SocketInterface import clientsocket
from ..MPLogger import loggingclient
import mitm_commands

from libmproxy import controller
import Queue
import sys
import traceback


class InterceptingMaster (controller.Master):
    """
    Customized MITMProxy
    Extends the proxy controller to add some additional
    functionality for handling /logging requests and responses

    Inspired by the following example. Note the gist has a lot of bugs.
    https://gist.github.com/dannvix/5285924
    """

    def __init__(self, server, visit_id_queue, browser_params, manager_params, status_queue):
        self.browser_params = browser_params
        self.manager_params = manager_params

        # Attributes used to flag the first-party domain
        self.visit_id_queue = visit_id_queue  # first-party domain provided by BrowserManager
        self.prev_visit_id, self.curr_visit_id = None, None  # previous and current top level domains
        self.prev_requests, self.curr_requests = set(), set()  # set of requests for previous and current site

        # Open a socket to communicate with DataAggregator
        self.db_socket = clientsocket()
        self.db_socket.connect(*manager_params['aggregator_address'])

        # Open a socket to communicate with LevelDBAggregator
        self.ldb_socket = None
        if browser_params['save_javascript']:
            self.ldb_socket = clientsocket()
            self.ldb_socket.connect(*manager_params['ldb_address'])

        # Open a socket to communicate with MPLogger
        self.logger = loggingclient(*manager_params['logger_address'])

        # Store status_queue for communication back to TaskManager
        self.status_queue = status_queue

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
        if self.curr_visit_id is None:  # proxy is fresh, need to get first-party domain right away
            self.curr_visit_id = self.visit_id_queue.get()
        elif not self.visit_id_queue.empty():  # new FP has been visited
            # drains the queue to get rid of stale messages from previous site
            while self.load_process_message(q, timeout):
                pass

            self.prev_requests, self.curr_requests = self.curr_requests, set()
            self.prev_visit_id, self.curr_visit_id = self.curr_visit_id, self.visit_id_queue.get()

        self.load_process_message(q, timeout)

    def run(self):
        """ Light wrapper around run with error printing """
        try:
            controller.Master.run(self)
        except KeyboardInterrupt:
            print 'KeyboardInterrupt received. Shutting down'
            self.shutdown()
            sys.exit(0)
        except Exception:
            excp = traceback.format_exception(*sys.exc_info())
            self.logger.critical('BROWSER %i: Exception. Shutting down proxy!\n%s' % (self.browser_params['crawl_id'], excp))
            self.status_queue.put(('FAILED', None))
            self.shutdown()
            raise

    def handle_request(self, msg):
        """ Receives HTTP request, and sends it to logging function """
        msg.reply()
        self.curr_requests.add(msg.request)
        mitm_commands.process_general_mitm_request(self.db_socket,
                                                   self.browser_params,
                                                   self.curr_visit_id,
                                                   msg)

    # Record data from HTTP responses
    def handle_response(self, msg):
        """ Receives HTTP response, and sends it to logging function """
        msg.reply()

        # attempts to get the top url visit id, based on the request object
        if msg.request in self.prev_requests:
            visit_id = self.prev_visit_id
            self.prev_requests.remove(msg.request)
        elif msg.request in self.curr_requests:
            visit_id = self.curr_visit_id
            self.curr_requests.remove(msg.request)
        else:  # ignore responses for which we cannot match the request
            return
        mitm_commands.process_general_mitm_response(self.db_socket,
                                                    self.ldb_socket,
                                                    self.logger,
                                                    self.browser_params,
                                                    visit_id, msg)
