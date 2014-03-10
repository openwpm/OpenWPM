# Customized MITMProxy
# Extends the proxy controller to add some additional
# functionality to handling requests and responses
from libmproxy import controller
import sys
import mitm_commands
import Queue

# Inspired by the following example. Note the gist has a lot of bugs.
# https://gist.github.com/dannvix/5285924
class InterceptingMaster (controller.Master):
    def __init__(self, server, crawl_id, url_queue, db_command_queue):
        self.crawl_id = crawl_id
        
        #Queue for crawler to push state data
        self.url_queue = url_queue
        self.top_url = None

        # Queue to communicate to DataAggregator
        self.db_queue = db_command_queue

        controller.Master.__init__(self, server)

    # loads all the messages in the queue
    # wrapper around old tick
    def load_all_messages(self, q):
        changed = False
        try:
            # This endless loop runs until the 'Queue.Empty'
            # exception is thrown. If more than one request is in
            # the queue, this speeds up every request by 0.1 seconds,
            # because get_input(..) function is not blocking.
            while True:
                # Small timeout to prevent pegging the CPU
                msg = q.get(1.0)
                controller.Master.handle(self, msg)
                changed = True
        except Queue.Empty:
            pass
        return changed

    # new tick function used to label top level domains and avoid race conditions when doing so
    def tick(self, q):
        # special case - we are changing the top level domain from one already existing
        # then we should load everything in the queue, then change top level domain
        if self.top_url is not None and not self.url_queue.empty():
            self.load_all_messages(q)
            self.top_url = self.url_queue.get()
        else :
            # first time we load a message with a blank top-level domain
            # we will need to load this domain before processing single message
            if self.top_url is None:
                self.top_url = self.url_queue.get()

            # finally, try to load the message
            try:
                msg = q.get(timeout=0.01)
                controller.Master.handle(self, msg)
            except Queue.Empty:
                pass

    # The while True lets you handle expections and restart the
    # proxy. Not using it right now, but it could be helpful.
    def run(self):
        while True:
            try:
                controller.Master.run(self)
            except KeyboardInterrupt:
                print 'KeyboardInterrupt received. Shutting down'
                self.shutdown()
                sys.exit(0)
            except Exception as ex:
                #print 'Exception. Intercepting proxy restarted!'
                print str(ex)
                #pass #Good way to get into infinite loops
                print 'Exception. Shutting down proxy!'
                self.shutdown()
                raise

    # Record data from requests
    def handle_request(self, msg):
        msg.reply()

        #Grab the correct top_url for this request
        #if self.top_url is None or not self.url_queue.empty():
        #    url = self.url_queue.get()
        #    self.top_url = url

        mitm_commands.process_general_mitm_request(self.db_queue, self.crawl_id, self.top_url, msg)

    #Record data from responses
    def handle_response(self, msg):
        msg.reply()

        #Grab the correct top_url for this response
        #if self.top_url is None or not self.url_queue.empty():
        #    url = self.url_queue.get()
        #    self.top_url = url

        mitm_commands.process_general_mitm_response(self.db_queue, self.crawl_id, self.top_url, msg)