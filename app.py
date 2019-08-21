from flask import Flask, render_template, Response
from trigger_server import TriggerServer
from stream_receiver import StreamReceiversPool


class StreamEndApp(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.trigger_server = TriggerServer(port=8888, start_data_port=10000)
        self._routes()
        self.stream_receivers = StreamReceiversPool()

    def _routes(self):
        self.route('/')(self.index)
        self.route('/video/<int:index>')(self.video_source)

    def index(self):
        stream_count = self.trigger_server.send_data_get_stream_count()
        return render_template('index.html', stream_count=stream_count)

    def video_source(self, index):
        return Response(self.jpeg_stream(index),
                        mimetype='multipart/x-mixed-replace; boundary=jpg')

    def jpeg_stream(self, index):
        receiver = self.stream_receivers.get_receiver(
            index,
            self.trigger_server.start_data_port + index
        )
        while True:
            img = receiver.get_img()
            yield (b'--jpg\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')


if __name__ == '__main__':
    app = StreamEndApp()
    try:
        app.trigger_server.start()
        app.debug = True
        app.run(debug=True, host='0.0.0.0', use_reloader=False, threaded=True)
    finally:
        app.trigger_server.stop()
