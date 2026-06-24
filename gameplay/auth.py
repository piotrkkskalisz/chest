from database.database import create_user, get_user
import bcrypt

def register(username: str, password: str) -> int | None:
    """Create a new user and return their ID, if something go wrong return None"""
    username = username.strip()
    if not username or not password:
        return None
    if get_user(username) is not None:
        return None

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    create_user(username, password_hash)
    user = get_user(username)
    return user[0] if user else None


def login(username: str, password: str) -> int | None:
    """Return the user's ID if the credentials are valid."""
    username = username.strip()
    if not username or not password:
        return None

    user = get_user(username)
    if user is None:
        return None

    password_hash = user[2]
    if bcrypt.checkpw(password.encode(), password_hash.encode()):
        return user[0]
    return None