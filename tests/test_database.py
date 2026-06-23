from database import database


def test_create_and_get_user(temp_db):
    database.create_user("alice", "secret")
    user = database.get_user("alice")
    assert user is not None
    assert user[1] == "alice"
    assert user[2] == "secret"


def test_get_missing_user_returns_none(temp_db):
    assert database.get_user("nobody") is None


def test_save_and_load_game(temp_db):
    database.create_user("bob", "pwd")
    owner_id = database.get_user("bob")[0]
    database.save_game(owner_id, "1. e4 e5 *")

    games = database.load_all_games(owner_id)
    assert len(games) == 1
    game_id = games[0][0]
    assert database.load_game(game_id) == "1. e4 e5 *"


def test_load_all_games_isolated_per_user(temp_db):
    database.create_user("u1", "p")
    database.create_user("u2", "p")
    id1 = database.get_user("u1")[0]
    id2 = database.get_user("u2")[0]
    database.save_game(id1, "game-of-u1")

    assert len(database.load_all_games(id1)) == 1
    assert database.load_all_games(id2) == []


def test_load_missing_game_returns_none(temp_db):
    assert database.load_game(9999) is None
