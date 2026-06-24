import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gameplay.game_logic import game
from database import database


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

def create_user_game_with_save(username: str = "user1", moves: tuple[tuple[str, str], ...]= (("e2", "e4"), ("e7", "e5"))) -> tuple[int, int]:
    password_hash = "fake_hash"
    user_id = database.create_user(username, password_hash)
    chess_game = game.Game(user_id = user_id)

    for move in moves:
        chess_game.make_move_between(*move)
    
    game_saves_id = chess_game.save_game()
    return user_id, game_saves_id


def test_load_saved_game(temp_db):
    user_id, game_id = create_user_game_with_save()
    loaded = game.Game(user_id = user_id)
    loaded.load_game(game_id)
    assert loaded.move_history == ["e4", "e5"]


def test_load_requires_logged_user(temp_db):
    _, game_id = create_user_game_with_save()
    with pytest.raises(ValueError):
        new_game = game.Game()
        new_game.load_game(game_id)


def test_cannot_load_game_without_save(temp_db):
    non_existing_game_id  = 1
    user_id = database.create_user("u2", "fake_hash")

    with pytest.raises(ValueError):
        new_game = game.Game(user_id = user_id)
        new_game.load_game(non_existing_game_id )

def test_users_cannot_load_each_other_games(temp_db):
    user1_id, game1_id = create_user_game_with_save()
    user2_id, game2_id = create_user_game_with_save("user2", (("a2", "a3"), ("a7", "a5"), ("a3", "a4")))

    with pytest.raises(ValueError):
        new_game = game.Game(user_id = user1_id)
        new_game.load_game(game2_id)
        
    with pytest.raises(ValueError):
        new_game = game.Game(user_id = user2_id)
        new_game.load_game(game1_id)