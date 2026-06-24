import sqlite3
from pathlib import Path
import platform
import os

USE_APPDATA_DB = True

if(USE_APPDATA_DB):
    if platform.system() == "Windows":
        APP_DIR = Path(os.environ["LOCALAPPDATA"]) / "Szachy"
    else:
        APP_DIR = Path.home() / ".szachy"
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = APP_DIR / "database.sqlite"
else:
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = BASE_DIR / "database" / "database.sqlite"

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_GAMES_TABLE = """
CREATE TABLE IF NOT EXISTS Games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    pgn TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id)
        REFERENCES Users(id)
        ON DELETE CASCADE
);
"""

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database() -> None:
    with _connect() as conn:
        conn.execute(CREATE_USERS_TABLE)
        conn.execute(CREATE_GAMES_TABLE)
        conn.commit()

def create_user(username: str, password_hash: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO Users(username, password_hash)
            VALUES (?, ?);
            """,
            (username, password_hash)
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid

def get_user(username: str) -> tuple | None:
    """Return the user's ID, username, password hash and creation date, or None if the user does not exist."""
    with _connect() as conn:
        return conn.execute(
            """
            SELECT *
            FROM Users
            WHERE username = ?;
            """,
            (username,)
        ).fetchone()

def load_game(user_id: int, game_id: int) -> str | None:
    """Return the PGN of the specified game, or None if it does not exist or does not belong to the user."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT pgn
            FROM Games
            WHERE id = ? AND owner_id = ?;
            """,
            (game_id, user_id)
        ).fetchone()

    return row[0] if row else None


def load_all_games(owner_id: int)  -> list[tuple]:
    """Return a list of (game_id, creation_date) tuples for the specified user."""
    with _connect() as conn:
        return conn.execute(
            """
            SELECT id, created_at
            FROM Games
            WHERE owner_id = ?
            ORDER BY created_at DESC;
            """,
            (owner_id,)
        ).fetchall()

def save_game(user_id:int, pgn: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO Games(owner_id, pgn)
            VALUES (?, ?);
            """,
            (user_id, pgn)
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid

if __name__ == "__main__":
    init_database()
