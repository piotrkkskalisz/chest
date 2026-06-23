from gameplay import auth


def test_register_new_user(temp_db):
    user_id = auth.register("alice", "secret")
    assert isinstance(user_id, int)


def test_register_duplicate_username_rejected(temp_db):
    assert auth.register("alice", "secret") is not None
    assert auth.register("alice", "other") is None


def test_register_rejects_empty_input(temp_db):
    assert auth.register("", "secret") is None
    assert auth.register("alice", "") is None
    assert auth.register("   ", "secret") is None


def test_login_success(temp_db):
    auth.register("bob", "pwd12345")
    assert auth.login("bob", "pwd12345") is not None


def test_login_wrong_password(temp_db):
    auth.register("bob", "pwd12345")
    assert auth.login("bob", "wrong") is None


def test_login_unknown_user(temp_db):
    assert auth.login("ghost", "whatever") is None


def test_login_trims_whitespace(temp_db):
    auth.register("carol", "pwd12345")
    assert auth.login("  carol  ", "pwd12345") is not None
