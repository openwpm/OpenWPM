import socketio
import eventlet
import eventlet.wsgi
import threading

def startSocketServer(browser_params={'js_instrument':True, 'cookie_instrument': True, 'cp_instrument': True}):
    sio = socketio.Server(async_mode='eventlet')
    @sio.on('connect', namespace='/openwpm')
    def connect(sid, environ):
        print("connect ", sid)
        sio.emit('config',{'js':browser_params['js_instrument'], 'cookie': browser_params['cookie_instrument'], 'cp': browser_params['cp_instrument']},namespace='/openwpm')

    @sio.on('sql', namespace='/openwpm')
    def message(sid, data):
        print("sql ", data)
        dbport.send(data)

    @sio.on('disconnect', namespace='/openwpm')
    def disconnect(sid):
        print('disconnect ', sid)

    wst = threading.Thread(target=serve, args=(sio,))
    wst.daemon = True
    wst.start()


def serve(_sio):
    try:
        # Silence repeated socket attempts
        app = socketio.Middleware(_sio)
        eventlet.wsgi.server(eventlet.listen(('', 7331)), app, log_output=False)
    except:
        pass


if __name__ == '__main__':
    startSocketServer()
    startSocketServer()
