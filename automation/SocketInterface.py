import Queue
import threading
import traceback
import socket
import struct
import json
import dill

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
        a 4-byte integer to specify the message length and 1-byte character
        to indicate the type of serialization applied to the message.

        Supported serialization formats:
            'n' : no serialization
            'd' : dill pickle
            'j' : json
        """
        if self.verbose:
            print "Thread: " + str(threading.current_thread()) + " connected to: " + str(address)
        try:
            while True:
                msg = self.receive_msg(client, 5)
                msglen, serialization = struct.unpack('>Lc', msg)
                if self.verbose:
                    print "Msglen: " + str(msglen) + " is_serialized: " + str(serialization != 'n')
                msg = self.receive_msg(client, msglen)
                if serialization != 'n':
                    try:
                        if serialization == 'd': # dill serialization
                            msg = dill.loads(msg)
                        elif serialization == 'j': # json serialization
                            try:
                                msg = json.loads(msg)
                            except UnicodeDecodeError:
                                try:
                                    msg = json.loads(unicode(msg, 'ISO-8859-1', 'ignore'))
                                except ValueError:
                                    print "****** Unrecognized character encoding during de-serialization."
                                    continue
                            except ValueError as e:
                                try:
                                    msg = json.loads(unicode(msg, 'utf-8', 'ignore'))
                                except ValueError:
                                    print "****** Unrecognized character encoding during de-serialization."
                                    continue
                        else:
                            print "Unrecognized serialization type: %s" % serialization
                            continue
                    except (UnicodeDecodeError, ValueError) as e:
                        print "Error de-serializing message: %s \n %s" % (
                                msg, traceback.format_exc(e))
                        continue
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
    """A client socket for sending messages"""
    def __init__(self, serialization='json', verbose=False):
        """ `serialization` specifies the type of serialization to use for
        non-str messages. Supported formats:
            * 'json' uses the json module. Cross-language support. (default)
            * 'dill' uses the dill pickle module. Python only.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if serialization != 'json' and serialization != 'dill':
            raise ValueError("Unsupported serialization type: %s" % serialization)
        self.serialization = serialization
        self.verbose = verbose

    def connect(self, host, port):
        if self.verbose: print "Connecting to: %s:%i" % (host, port)
        self.sock.connect((host, port))

    def send(self, msg):
        """
        Sends an arbitrary python object to the connected socket. Serializes
        using dill if not str, and prepends msg len (4-bytes) and
        serialization type (1-byte).
        """
        #if input not string, serialize to string
        if type(msg) is not str:
            if self.serialization == 'dill':
                msg = dill.dumps(msg)
                serialization = 'd'
            elif self.serialization == 'json':
                msg = json.dumps(msg)
                serialization = 'j'
            else:
                raise ValueError("Unsupported serialization type set: %s" % serialization)
        else:
            serialization = 'n'

        if self.verbose: print "Sending message with serialization %s" % serialization

        #prepend with message length
        msg = struct.pack('>Lc', len(msg), serialization) + msg
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
        raw_input("Press enter to exit...")
        sock.close()
    elif sys.argv[1] == 'c':
        host = raw_input("Enter the host name:\n")
        port = raw_input("Enter the port:\n")
        serialization = raw_input("Enter the serialization type (default: 'json'):\n")
        if serialization == '':
            serialization = 'json'
        sock = clientsocket(serialization=serialization)
        sock.connect(host, int(port))
        msg = None

        # some predefined messages
        tuple_msg = ('hello','world')
        list_msg = ['hello','world']
        dict_msg = {'hello':'world'}
        def function_msg(x): return x

        # read user input
        while msg != "quit":
            msg = raw_input("Enter a message to send:\n")
            if msg == 'tuple':
                sock.send(tuple_msg)
            elif msg == 'list':
                sock.send(list_msg)
            elif msg == 'dict':
                sock.send(dict_msg)
            elif msg == 'function':
                sock.send(function_msg)
            else:
                sock.send(msg)
        sock.close()
