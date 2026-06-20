import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gameplay.game_logic import game


def test_initial_state():
    chess_game = game.Game()
    assert chess_game.current_player == game.WHITE
    assert chess_game.status() == game.NORMAL_STATUS
    assert len(chess_game.board_to_display()) == 32


def test_legal_targets_for_pawn():
    chess_game = game.Game()
    targets = chess_game.position_legal_from("e2")
    assert set(targets) == {"e3", "e4"}


def test_illegal_move_rejected():
    chess_game = game.Game()
    assert chess_game.make_move_between("e2", "e5") is False
    assert chess_game.current_player == game.WHITE


def test_legal_move_and_history():
    chess_game = game.Game()
    assert chess_game.make_move_between("e2", "e4") is True
    assert chess_game.current_player == game.BLACK
    assert chess_game.move_history == ["e4"]
    assert chess_game.last_move == "e2e4"


def test_fools_mate_checkmate():
    chess_game = game.Game()
    for origin, target in (("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")):
        assert chess_game.make_move_between(origin, target)
    assert chess_game.status() == game.CHECKMATE_STATUS
    assert chess_game.is_game_over()
    assert chess_game.winner() == game.BLACK


def test_promotion_detection():
    chess_game = game.Game()
    chess_game.load_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    assert chess_game.needs_promotion("a7", "a8")
    assert chess_game.make_move_between("a7", "a8", "Q")
    display = chess_game.board_to_display()
    assert display["a8"] == ("Q", game.WHITE)


def test_en_passant():
    chess_game = game.Game()
    chess_game.load_fen("rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3")
    assert chess_game.make_move_between("e5", "f6")
    assert "f5" not in chess_game.board_to_display()


def test_castling_available():
    chess_game = game.Game()
    chess_game.load_fen("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    assert "g1" in chess_game.position_legal_from("e1")
    assert chess_game.make_move_between("e1", "g1")
    display = chess_game.board_to_display()
    assert display["g1"] == ("K", game.WHITE)
    assert display["f1"] == ("R", game.WHITE)


def test_pgn_round_trip(tmp_path):
    chess_game = game.Game()
    chess_game.make_move_between("e2", "e4")
    chess_game.make_move_between("e7", "e5")
    path = tmp_path / "game.pgn"
    chess_game.save_pgn(str(path))
    loaded = game.Game()
    loaded.load_pgn(str(path))
    assert loaded.move_history == ["e4", "e5"]
