# Customized MITMProxy
# Extends the proxy controller to add some additional
# functionality to handling requests and responses
from ..SocketInterface import clientsocket
from libmproxy import controller
import sys
import Queue
import mitm_commands
from tld import get_tld

# Inspired by the following example. Note the gist has a lot of bugs.
# https://gist.github.com/dannvix/5285924
class InterceptingMaster (controller.Master):
    def __init__(self, server, crawl_id, url_queue, db_socket_address):
        self.crawl_id = crawl_id
        
        # Attributes used to flag the first-party domain
        self.url_queue = url_queue  # first-party domain provided by BrowserManager
        self.curr_top_url = None  # current first-party url
        self.new_top_url = None  # first-party url that BrowserManager just claimed to have visited
        self.changed = False  # used to flag that new site has been visited so proxy looks for new site's traffic

        # Open a socket to communicate with DataAggregator
        self.db_socket = clientsocket()
        self.db_socket.connect(*db_socket_address)

        controller.Master.__init__(self, server)

    # new tick function used to label first-party domains and avoid race conditions when doing so
    def tick(self, q):
        if self.curr_top_url is None:  # proxy is fresh, need to get first-party domain right away
            self.new_top_url = self.url_queue.get()
            self.curr_top_url = self.new_top_url
        elif not self.url_queue.empty():  # new FP has been visited -> should prepare to see traffic from new site
            self.new_top_url = self.url_queue.get()
            self.changed = True

        # try to load/process message as usual
        try:
            msg = q.get(timeout=0.01)
            controller.Master.handle(self, msg)
        except Queue.Empty:
            pass

    # Light wrapper around run with error printing
    def run(self):
        try:
            controller.Master.run(self)
        except KeyboardInterrupt:
            print 'KeyboardInterrupt received. Shutting down'
            self.shutdown()
            sys.exit(0)
        except Exception as ex:
            print str(ex)
            print 'Exception. Shutting down proxy!'
            self.shutdown()
            raise

    # Record data from HTTP requests
    def handle_request(self, msg):
        msg.reply()

        # use heuristic to detect that we are now indeed seeing traffic from newly-visited site (if applicable)
        if self.changed:
            #print get_tld(self.new_top_url, fail_silently=True) + "\t" + get_tld(msg.get_url(), fail_silently=True)
            if get_tld(self.new_top_url, fail_silently=True) == get_tld(msg.get_url(), fail_silently=True):
                self.curr_top_url = self.new_top_url
                self.changed = False

        mitm_commands.process_general_mitm_request(self.db_socket, self.crawl_id, self.curr_top_url, msg)

    # Record data from HTTP responses
    def handle_response(self, msg):
        msg.reply()

        mitm_commands.process_general_mitm_response(self.db_socket, self.crawl_id, self.curr_top_url, msg)
