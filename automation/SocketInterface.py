import Queue
import threading
import socket
import struct
import cPickle

#TODO - Implement a cleaner shutdown for server socket
# see: https://stackoverflow.com/questions/1148062/python-socket-accept-blocks-prevents-app-from-quitting

class serversocket:
    """
    A server socket to recieve and process string messages
    from client sockets to a central queue
    """
    def __init__(self, verbose=False):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', 0))
        self.sock.listen(10)  # queue a max of n connect requests
        self.verbose = verbose
        self.queue = Queue.Queue()
        if self.verbose:
            print "Server bound to: " + str(self.sock.getsockname())
    
    def start_accepting(self):
        """ Start the listener thread """
        thread = threading.Thread(target=self._accept, args=())
        thread.daemon = True  # stops from blocking shutdown
        thread.start()

    def _accept(self):
        """ Listen for connections and pass handling to a new thread """
        while True:
            (client, address) = self.sock.accept()
            thread = threading.Thread(target=self._handle_conn, args=(client, address))
            thread.daemon = True
            thread.start()
            
    def _handle_conn(self, client, address):
        """
        Recieve messages and pass to queue. Messages are prefixed with
        a 4-byte integer to specify the message length and 1-byte boolean
        to indicate pickling.
        """
        if self.verbose:
            print "Thread: " + str(threading.current_thread()) + " connected to: " + str(address)
        try:
            while True:
                msg = self.receive_msg(client, 5)
                msglen, is_pickled = struct.unpack('>I?', msg)
                msg = self.receive_msg(client, msglen)
                if is_pickled:
                    msg = cPickle.loads(msg)
                self.queue.put(msg)
        except RuntimeError:
            if self.verbose:
                print "Client socket: " + str(address) + " closed"

    def receive_msg(self, client, msglen):
        msg = ''
        while len(msg) < msglen:
            chunk = client.recv(msglen-len(msg))
            if chunk == '':
                raise RuntimeError("socket connection broken")
            msg = msg + chunk
        return msg

    def close(self):
        self.sock.close()

class clientsocket:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host, port):
        self.sock.connect((host, port))

    def send(self, msg):
        """
        Sends an arbitrary python object to the connected socket. Pickles if 
        not str, and prepends msg len (4-bytes) and pickle status (1-byte).
        """
        #if input not string, pickle
        if type(msg) is not str:
            msg = cPickle.dumps(msg)
            is_pickled = True
        else:
            is_pickled = False
        
        #prepend with message length
        msg = struct.pack('>I?', len(msg), is_pickled) + msg
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
    
    def close(self):
        self.sock.close()

if __name__ == '__main__':
    import sys

    #Just for testing
    if sys.argv[1] == 's':
        sock = serversocket(verbose=True)
        sock.start_accepting()
    elif sys.argv[1] == 'c':
        sock = clientsocket()
