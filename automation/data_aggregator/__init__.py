from ..SocketInterface import ServerSocket


class DataAggregator:
    def startup(self):
        """Run listener startup tasks

        Note: Child classes should call this method"""
        self.sock = ServerSocket(name=type(self).__name__)
        self.status_queue.put(self.sock.sock.getsockname())
        self.sock.start_accepting()
        self.record_queue = self.sock.queue
