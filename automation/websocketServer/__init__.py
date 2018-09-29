import socketio
import eventlet
import eventlet.wsgi
from multiprocess import Process


def startSocketServer(
    browser_params={
        'js_instrument': True,
        'cookie_instrument': True,
        'cp_instrument': True},
        log_output=False,
        daemon=True):
    sio = socketio.Server(async_mode='eventlet')

    @sio.on('connect', namespace='/openwpm')
    def connect(sid, environ):
        print("connect ", sid)
        sio.emit('config',
                 {'js': browser_params['js_instrument'],
                  'cookie': browser_params['cookie_instrument'],
                  'cp': browser_params['cp_instrument']},
                 namespace='/openwpm')

    @sio.on('sql', namespace='/openwpm')
    def message(sid, data):
        print("sql ", data)
        dbport.send(data)

    @sio.on('disconnect', namespace='/openwpm')
    def disconnect(sid):
        print('disconnect ', sid)

    args = (sio, log_output)
    socket_server_process = Process(target=serve, args=args)
    socket_server_process.daemon = daemon
    socket_server_process.start()


def serve(_sio, log_output):
    try:
        # Silence repeated socket attempts
        app = socketio.Middleware(_sio)
        eventlet.wsgi.server(
            eventlet.listen(
                ('', 7331)), app, log_output=log_output)
    except BaseException:
        pass


if __name__ == '__main__':
    startSocketServer(log_output=True, daemon=False)
