import socket
import time
import logging
import threading

from event_system import EventSystem


class TriggerServer:
    def __init__(self, port, start_data_port):
        self.port = port
        self.start_data_port = start_data_port
        EventSystem.send_event = threading.Event()
        self._stop_event = threading.Event()
        self.streams_count = None

    def send_data_get_stream_count(self):
        EventSystem.send_event.set()
        while self.streams_count is None:
            time.sleep(0.1)
        return int(self.streams_count.decode())

    def close_data(self):
        EventSystem.send_event.clear()

    def run(self):
        with socket.socket() as trigger_socket:
            trigger_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            trigger_socket.bind(('0.0.0.0', self.port))
            trigger_socket.listen(5)
            print('Waiting for trigger connection on {}'.format(self.port))
            conn, addr = trigger_socket.accept()
            with conn:
                while True:
                    print('Waiting for send event')
                    while not EventSystem.send_event.is_set():
                        if self._stop_event.is_set():
                            print("Exiting trigger server")
                            return
                        time.sleep(0.1)
                    print('triggering stream upload')
                    conn.send(b'send_data')
                    self.streams_count = conn.recv(10)
                    print('received stream count: {}'.format(self.streams_count))
                    conn.send(str(self.start_data_port).encode())
                    print('Waiting for event clear')
                    while EventSystem.send_event.is_set():
                        if self._stop_event.is_set():
                            print("Exiting trigger server")
                            return
                        time.sleep(0.1)
                    conn.send(b'close_data')
                    self.streams_count = None
                    print('Closed sent')

    def start(self):
        threading.Thread(target=self.run).start()

    def stop(self):
        self._stop_event.set()
