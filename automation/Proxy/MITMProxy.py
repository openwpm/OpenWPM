# Customized MITMProxy
# Extends the proxy controller to add some additional
# functionality to handling requests and responses
from libmproxy import controller
import sys
import mitm_commands

# Inspired by the following example. Note the gist has a lot of bugs.
# https://gist.github.com/dannvix/5285924
class InterceptingMaster (controller.Master):
    def __init__(self, server, crawl_id, url_queue, db_command_queue):
        self.crawl_id = crawl_id
        
        #Queue for crawler to push state data
        self.url_queue = url_queue
        self.top_url = None

        # Queue to communicate to database oracle
        self.db_queue = db_command_queue

        controller.Master.__init__(self, server)

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
        if self.top_url is None or not self.url_queue.empty():
            url = self.url_queue.get()
            self.top_url = url

        mitm_commands.process_general_mitm_request(self.db_queue, self.crawl_id, self.top_url, msg)

    #Record data from responses
    def handle_response(self, msg):
        msg.reply()

        #Grab the correct top_url for this response
        if self.top_url is None or not self.url_queue.empty():
            url = self.url_queue.get()
            self.top_url = url

        mitm_commands.process_general_mitm_response(self.db_queue, self.crawl_id, self.top_url, msg)