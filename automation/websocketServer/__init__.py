import socketio
import eventlet
import eventlet.wsgi
from multiprocess import Process


def startSocketServer(
        browser_params={
            'cookie_instrument': True,
            'js_instrument': True,
            'http_instrument': True,
            'save_javascript': True,
            'save_all_content': True
        },
        manager_params={
            'logger_address': 'foo',
            'aggregator_address': 'foo',
            'ldb_address': 'foo',
            'testing': True
        },
        log_output=False,
        verbose=False,
        daemon=True):
    sio = socketio.Server(async_mode='eventlet', logger=log_output, engineio_logger=verbose)

    class OpenWpmExtensionListenConfigurationNamespace(socketio.Namespace):
        def on_connect(self, sid, environ):
            print "Client connected - sid, environ['HTTP_USER_AGENT']" + sid + ", " + environ['HTTP_USER_AGENT']
            pass

        def on_request(self, sid):
            print "Sending config over socket"
            self.emit('config', {'browser_params': browser_params, 'manager_params': manager_params})

        def on_disconnect(self, sid):
            pass

    sio.register_namespace(OpenWpmExtensionListenConfigurationNamespace('/openwpm-extension-listen-configuration'))

    # TODO: Re-route received records to the data aggregators

    class OpenWpmExtensionSendLogNamespace(socketio.Namespace):
        def on_connect(self, sid, environ):
            print "Client connected - sid, environ['HTTP_USER_AGENT']" + sid + ", " + environ['HTTP_USER_AGENT']

        def on_disconnect(self, sid):
            pass

        def on_record(self, sid, record):
            print "record received over socket", record

    class OpenWpmExtensionSendDataNamespace(socketio.Namespace):
        def on_connect(self, sid, environ):
            print "Client connected - sid, environ['HTTP_USER_AGENT']" + sid + ", " + environ['HTTP_USER_AGENT']

        def on_disconnect(self, sid):
            pass

        def on_record(self, sid, record):
            print "record received over socket", record

    class OpenWpmExtensionSendLdbNamespace(socketio.Namespace):
        def on_connect(self, sid, environ):
            print "Client connected - sid, environ['HTTP_USER_AGENT']" + sid + ", " + environ['HTTP_USER_AGENT']

        def on_disconnect(self, sid):
            pass

        def on_record(self, sid, record):
            print "record received over socket", record

    sio.register_namespace(OpenWpmExtensionSendLogNamespace('/openwpm-extension-send-log'))
    sio.register_namespace(OpenWpmExtensionSendDataNamespace('/openwpm-extension-send-data'))
    sio.register_namespace(OpenWpmExtensionSendLdbNamespace('/openwpm-extension-send-ldb'))

    args = (sio, log_output)
    socket_server_process = Process(target=serve, args=args)
    socket_server_process.daemon = daemon
    socket_server_process.start()

    print "Socket server deployed with pid " + str(socket_server_process.pid)

    return sio


def serve(_sio, log_output):
    app = socketio.Middleware(_sio)
    eventlet.wsgi.server(
        eventlet.listen(
            ('', 7331)), app, log_output=log_output)


if __name__ == '__main__':
    print("Starting socket server standalone")
    startSocketServer(log_output=True, verbose=False, daemon=False)
