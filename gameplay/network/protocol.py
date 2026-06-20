import json
import socket

DEFAULT_PORT = 50007
ENCODING = "utf-8"
TERMINATOR = "\n"

TYPE_JOIN = "join"
TYPE_ASSIGNED = "assigned"
TYPE_STATE = "state"
TYPE_MOVE = "move"
TYPE_ILLEGAL = "illegal"
TYPE_RESIGN = "resign"
TYPE_GAME_OVER = "game_over"
TYPE_ERROR = "error"
TYPE_CHAT = "chat"


def join_message() -> dict:
    return {"type": TYPE_JOIN}


def assigned_message(color: str) -> dict:
    return {"type": TYPE_ASSIGNED, "color": color}


def move_message(from_square: str, to_square: str, promotion: str | None = None) -> dict:
    return {
        "type": TYPE_MOVE,
        "from": from_square,
        "to": to_square,
        "promotion": promotion,
    }


def state_message(fen: str, status: str, turn: str, history: list[str],
                  last_move: str | None, winner: str | None) -> dict:
    return {
        "type": TYPE_STATE,
        "fen": fen,
        "status": status,
        "turn": turn,
        "history": history,
        "last_move": last_move,
        "winner": winner,
    }


def illegal_message() -> dict:
    return {"type": TYPE_ILLEGAL}


def resign_message() -> dict:
    return {"type": TYPE_RESIGN}


def game_over_message(reason: str, winner: str | None) -> dict:
    return {"type": TYPE_GAME_OVER, "reason": reason, "winner": winner}


def error_message(text: str) -> dict:
    return {"type": TYPE_ERROR, "message": text}


def chat_message(text: str) -> dict:
    return {"type": TYPE_CHAT, "text": text}


def encode(message: dict) -> bytes:
    return (json.dumps(message) + TERMINATOR).encode(ENCODING)


def send_message(connection: socket.socket, message: dict) -> None:
    connection.sendall(encode(message))


class MessageReader:
    def __init__(self, connection: socket.socket):
        self._connection = connection
        self._buffer = ""

    def read_messages(self) -> list[dict]:
        data = self._connection.recv(4096)
        if not data:
            raise ConnectionError("Connection closed by peer.")
        self._buffer += data.decode(ENCODING)
        messages: list[dict] = []
        while TERMINATOR in self._buffer:
            line, self._buffer = self._buffer.split(TERMINATOR, 1)
            line = line.strip()
            if line:
                messages.append(json.loads(line))
        return messages
