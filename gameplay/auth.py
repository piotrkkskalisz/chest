import bcrypt
from database.database import create_user, get_user


def register(username: str, password: str) -> int | None:
    """Creates a new user."""
    if get_user(username) is not None:
        return None

    password_hash = password#bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    create_user(username, password_hash)
    user = get_user(username)
    return user[0]


def login(username: str, password: str) -> int | None:
    """Logs the user in."""
    user = get_user(username)

    if user is None:
        return None

    password_hash = user[2]

    if password_hash == password:#bcrypt.checkpw(password.encode(), password_hash.encode()):
        return user[0]

    return None