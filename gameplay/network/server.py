import socket
import threading

import chess

from . import protocol
from ..game_logic import game


SPECTATOR = "spectator"
SEAT_ORDER = (game.WHITE, game.BLACK)


class ClientConnection:
    def __init__(self, connection: socket.socket, address, color: str):
        self.connection = connection
        self.address = address
        self.color = color
        self.reader = protocol.MessageReader(connection)


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = protocol.DEFAULT_PORT):
        self.host = host
        self.port = port
        self._server_socket: socket.socket | None = None
        self._clients: list[ClientConnection] = []
        self._board = chess.Board()
        self._history: list[str] = []
        self._winner: str | None = None
        self._over_reason: str | None = None
        self._lock = threading.RLock()
        self._running = False
        self._accept_thread: threading.Thread | None = None

    def start(self) -> int:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(8)
        self.port = self._server_socket.getsockname()[1]
        self._running = True
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()
        return self.port

    def _accept_loop(self) -> None:
        while self._running:
            try:
                connection, address = self._server_socket.accept()
            except OSError:
                break
            color = self._assign_color()
            client = ClientConnection(connection, address, color)
            with self._lock:
                self._clients.append(client)
            protocol.send_message(connection, protocol.assigned_message(color))
            self._send_state_to(client)
            thread = threading.Thread(target=self._client_loop, args=(client,), daemon=True)
            thread.start()

    def _assign_color(self) -> str:
        taken = {client.color for client in self._clients}
        for color in SEAT_ORDER:
            if color not in taken:
                return color
        return SPECTATOR

    def _client_loop(self, client: ClientConnection) -> None:
        try:
            while self._running:
                for message in client.reader.read_messages():
                    self._handle_message(client, message)
        except (ConnectionError, OSError):
            pass
        finally:
            self._remove_client(client)

    def _handle_message(self, client: ClientConnection, message: dict) -> None:
        kind = message.get("type")
        if kind == protocol.TYPE_MOVE:
            self._handle_move(client, message)
        elif kind == protocol.TYPE_RESIGN:
            self._handle_resign(client)

    def _handle_move(self, client: ClientConnection, message: dict) -> None:
        with self._lock:
            if self._winner is not None or self._over_reason is not None:
                return
            if client.color == SPECTATOR:
                protocol.send_message(client.connection, protocol.illegal_message())
                return
            if game.to_color(self._board.turn) != client.color:
                protocol.send_message(client.connection, protocol.illegal_message())
                return
            code = f"{message.get('from')}{message.get('to')}"
            promotion = message.get("promotion")
            if promotion:
                code += str(promotion).lower()
            if not self._apply_move(code):
                protocol.send_message(client.connection, protocol.illegal_message())
                return
        self._broadcast_state()
        self._check_game_over()

    def _apply_move(self, code: str) -> bool:
        try:
            move = chess.Move.from_uci(code)
        except ValueError:
            return False
        if move not in self._board.legal_moves:
            return False
        san = self._board.san(move)
        self._board.push(move)
        self._history.append(san)
        return True

    def _handle_resign(self, client: ClientConnection) -> None:
        with self._lock:
            if client.color == SPECTATOR or self._over_reason is not None:
                return
            self._winner = game.opposite(client.color)
            self._over_reason = "resign"
        self._broadcast_state()
        self._broadcast(protocol.game_over_message("resign", self._winner))

    def _check_game_over(self) -> None:
        with self._lock:
            if self._board.is_checkmate():
                self._winner = game.to_color(not self._board.turn)
                self._over_reason = "checkmate"
            elif self._board.is_stalemate():
                self._over_reason = "stalemate"
            elif (self._board.is_insufficient_material()
                  or self._board.is_seventyfive_moves()
                  or self._board.is_fivefold_repetition()):
                self._over_reason = "draw"
            reason = self._over_reason
            winner = self._winner
        if reason is not None:
            self._broadcast(protocol.game_over_message(reason, winner))

    def _state_payload(self) -> dict:
        last = self._board.move_stack[-1].uci() if self._board.move_stack else None
        if self._board.is_checkmate():
            status = game.CHECKMATE_STATUS
        elif self._board.is_stalemate():
            status = game.STALEMATE_STATUS
        elif self._board.is_check():
            status = game.CHECK_STATUS
        else:
            status = game.NORMAL_STATUS
        return protocol.state_message(
            self._board.fen(),
            status,
            game.to_color(self._board.turn),
            list(self._history),
            last,
            self._winner,
        )

    def _send_state_to(self, client: ClientConnection) -> None:
        with self._lock:
            payload = self._state_payload()
        try:
            protocol.send_message(client.connection, payload)
        except OSError:
            self._remove_client(client)

    def _broadcast_state(self) -> None:
        with self._lock:
            payload = self._state_payload()
        self._broadcast(payload)

    def _broadcast(self, message: dict) -> None:
        with self._lock:
            clients = list(self._clients)
        for client in clients:
            try:
                protocol.send_message(client.connection, message)
            except OSError:
                self._remove_client(client)

    def _remove_client(self, client: ClientConnection) -> None:
        with self._lock:
            if client in self._clients:
                self._clients.remove(client)
        try:
            client.connection.close()
        except OSError:
            pass

    def stop(self) -> None:
        self._running = False
        with self._lock:
            clients = list(self._clients)
        for client in clients:
            try:
                client.connection.close()
            except OSError:
                pass
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass


def local_ip_address() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()
