from database.database import create_user, get_user


def _clean(username: str) -> str:
    return (username or "").strip()


def register(username: str, password: str) -> int | None:
    username = _clean(username)
    if not username or not password:
        return None
    if get_user(username) is not None:
        return None

    password_hash = password
    create_user(username, password_hash)
    user = get_user(username)
    return user[0] if user else None


def login(username: str, password: str) -> int | None:
    username = _clean(username)
    if not username or not password:
        return None

    user = get_user(username)
    if user is None:
        return None

    password_hash = user[2]
    if password_hash == password:
        return user[0]
    return None
