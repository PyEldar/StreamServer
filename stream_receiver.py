import logging
import socket
import threading
import time

from event_system import EventSystem


class StreamReceiver:
    def __init__(self, port):
        self.thread = None
        self.img = None
        self.port = port
        self._last_access = 0
        self._event = threading.Event()
        print('Stream receiver initialized with port {}'.format(self.port))

    def get_img(self):
        self._last_access = time.time()
        if self.thread is None:
            print('Starting Stream receiver thread')
            self.thread = threading.Thread(target=self._receive)
            self.thread.start()
            while self.img is None:
                time.sleep(0.1)
        self._event.wait()
        self._event.clear()
        return self.img

    def _receive(self):
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as data_socket:
            data_socket.bind(('0.0.0.0', self.port))
            print('Waiting for connection on {}'.format(self.port))
            bytes_array = bytes()
            while EventSystem.send_event.is_set() and not time.time() - self._last_access > 5:
                chunk, addr = data_socket.recvfrom(8192)
                if not chunk:
                    print('No data, exiting')
                    break
                bytes_array += chunk
                a = bytes_array.find(b'\xff\xd8')
                b = bytes_array.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_array[a:b + 2]
                    bytes_array = bytes_array[b + 2:]
                    self.img = jpg
                    print("Got Image")
                    self._event.set()

        print('Exiting Receive thread on port {}'.format(self.port))
        self.thread = None
        self.img = None
        EventSystem.send_event.clear()


class StreamReceiversPool:
    def __init__(self):
        self.receivers = dict()

    def get_receiver(self, index, port):
        if not self.receivers.get(index):
            self.receivers[index] = StreamReceiver(port)
        return self.receivers.get(index)
