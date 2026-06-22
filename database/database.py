import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.sqlite"

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


def init_database() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(CREATE_USERS_TABLE)
        conn.execute(CREATE_GAMES_TABLE)
        conn.commit()

def create_user(username: str, password_hash: str) -> None:
    """    Creates a new user in the database.  """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO Users(username, password_hash)
            VALUES (?, ?);
            """,
            (username, password_hash)
        )

def get_user(username: str):
    """Returns the user with the given username or None if it does not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT *
            FROM Users
            WHERE username = ?;
            """,
            (username,)
        ).fetchone()

def load_game(game_id: int) -> str | None:
    """Returns the PGN of the selected game."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT pgn
            FROM Games
            WHERE id = ?;
            """,
            (game_id,)
        ).fetchone()

    return row[0] if row else None


def load_all_games(owner_id: int):
    """Returns all games belonging to the specified user."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT id, created_at
            FROM Games
            WHERE owner_id = ?
            ORDER BY created_at DESC;
            """,
            (owner_id,)
        ).fetchall()

def save_game(user_id:int, pgn: str):
    """Saves a game in PGN format for the specified user."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO Games(owner_id, pgn)
            VALUES (?, ?);
            """,
            (user_id, pgn)
        )

if __name__ == "__main__":
    init_database()

