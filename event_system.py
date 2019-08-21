import threading


class EventSystem:
    send_event = threading.Event()