import queue
import socket
import threading

from . import protocol


class NetworkClient:
    def __init__(self, host: str, port: int = protocol.DEFAULT_PORT):
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None
        self._reader: protocol.MessageReader | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self.inbox: "queue.Queue[dict]" = queue.Queue()
        self.color: str | None = None

    def connect(self, timeout: float = 5.0) -> None:
        self._socket = socket.create_connection((self.host, self.port), timeout=timeout)
        self._socket.settimeout(None)
        self._reader = protocol.MessageReader(self._socket)
        self._running = True
        protocol.send_message(self._socket, protocol.join_message())
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()

    def _receive_loop(self) -> None:
        try:
            while self._running:
                for message in self._reader.read_messages():
                    if message.get("type") == protocol.TYPE_ASSIGNED:
                        self.color = message.get("color")
                    self.inbox.put(message)
        except (ConnectionError, OSError):
            if self._running:
                self.inbox.put(protocol.error_message("Connection lost."))
        finally:
            self._running = False

    def send_move(self, from_square: str, to_square: str,
                  promotion: str | None = None) -> None:
        self._send(protocol.move_message(from_square, to_square, promotion))

    def send_resign(self) -> None:
        self._send(protocol.resign_message())

    def _send(self, message: dict) -> None:
        if self._socket is None:
            return
        try:
            protocol.send_message(self._socket, message)
        except OSError:
            self.inbox.put(protocol.error_message("Failed to send message."))

    def close(self) -> None:
        self._running = False
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
