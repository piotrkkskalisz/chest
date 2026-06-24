from database import database


def test_create_and_get_user(temp_db):
    hash = "secret_hash"
    database.create_user("alice", hash)
    user = database.get_user("alice")
    assert user is not None
    assert user[1] == "alice"
    assert user[2] == hash

def user_id(username: str) -> int:
    user = database.get_user(username)
    assert user is not None
    return user[0]

def test_get_missing_user_returns_none(temp_db):
    assert database.get_user("nobody") is None


def test_save_and_load_game(temp_db):
    database.create_user("bob", "fake_hash")

    owner_id = user_id("bob")
    database.save_game(owner_id, "1. e4 e5 *")

    games = database.load_all_games(owner_id)
    assert len(games) == 1
    game_id = games[0][0]
    assert database.load_game(owner_id, game_id) == "1. e4 e5 *"


def test_load_all_games_isolated_per_user(temp_db):
    database.create_user("u1", "fake_hash")
    database.create_user("u2", "fake_hash")

    id1 = user_id("u1")
    id2 = user_id("u2")

    database.save_game(id1, "game-of-u1")

    assert len(database.load_all_games(id1)) == 1
    assert database.load_all_games(id2) == []

def test_load_missing_game_returns_none(temp_db):
    user_id = database.create_user("u2", "fake_hash")

    assert database.load_game(user_id, 9999) is None
