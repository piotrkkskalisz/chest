import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gameplay.network import protocol
from gameplay.network.client import NetworkClient
from gameplay.network.server import GameServer


def _wait_for(client, message_type, timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            message = client.inbox.get(timeout=deadline - time.time())
        except Exception:
            break
        if message.get("type") == message_type:
            return message
    raise AssertionError(f"Did not receive {message_type}")


def test_color_assignment_and_move_flow():
    server = GameServer(host="127.0.0.1", port=0)
    port = server.start()
    white = NetworkClient("127.0.0.1", port)
    black = NetworkClient("127.0.0.1", port)
    try:
        white.connect()
        assigned_white = _wait_for(white, protocol.TYPE_ASSIGNED)
        assert assigned_white["color"] == "white"
        black.connect()
        assigned_black = _wait_for(black, protocol.TYPE_ASSIGNED)
        assert assigned_black["color"] == "black"

        white.send_move("e2", "e4")
        state = _wait_for(black, protocol.TYPE_STATE)
        while state.get("last_move") != "e2e4":
            state = _wait_for(black, protocol.TYPE_STATE)
        assert state["turn"] == "black"
        assert "e4" in state["history"]
    finally:
        white.close()
        black.close()
        server.stop()


def test_illegal_move_rejected_for_wrong_turn():
    server = GameServer(host="127.0.0.1", port=0)
    port = server.start()
    white = NetworkClient("127.0.0.1", port)
    black = NetworkClient("127.0.0.1", port)
    try:
        white.connect()
        _wait_for(white, protocol.TYPE_ASSIGNED)
        black.connect()
        _wait_for(black, protocol.TYPE_ASSIGNED)
        black.send_move("e7", "e5")
        rejected = _wait_for(black, protocol.TYPE_ILLEGAL)
        assert rejected["type"] == protocol.TYPE_ILLEGAL
    finally:
        white.close()
        black.close()
        server.stop()
