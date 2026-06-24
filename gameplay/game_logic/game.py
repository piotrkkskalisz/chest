import os
import platform
from pathlib import Path
from typing import Literal
from io import StringIO
import subprocess

try:
    from typing import override
except ImportError:
    def override(func):
        return func

from database import database

import chess
import chess.engine
import chess.pgn


BOARD_SIZE = 8
FILES = "abcdefgh"
SQUARE_CODE_SIZE = 2

WHITE = "white"
BLACK = "black"

NORMAL_STATUS = "normal"
CHECK_STATUS = "check"
CHECKMATE_STATUS = "checkmate"
STALEMATE_STATUS = "stalemate"
DRAW_STATUS = "draw"

DEFAULT_ELO = 1320


PieceType = Literal["P", "N", "B", "R", "Q", "K"]
Color = Literal["white", "black"]
Square = str
PieceDisplay = tuple[PieceType, Color]
BoardFormat = dict[Square, PieceDisplay]


_PIECE_LETTERS: dict[int, PieceType] = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
    chess.KING: "K",
}


def _to_piece_type(piece: chess.Piece) -> PieceType:
    return _PIECE_LETTERS[piece.piece_type]


def to_color(color_bool: bool) -> Color:
    return WHITE if color_bool else BLACK


def opposite(color: Color) -> Color:
    return BLACK if color == WHITE else WHITE

def find_stockfish() -> str | None:
    """Return the path to the Stockfish executable or None if it cannot be found."""
    here = Path(__file__).resolve().parent / "stockfish"
    candidates: list[Path] = []
    if here.is_dir():
        for entry in here.iterdir():
            if entry.is_file() and entry.name.lower().startswith("stockfish"):
                candidates.append(entry)
    if candidates:
        executables = [c for c in candidates if os.access(c, os.X_OK)] or candidates
        if platform.system() == "Windows":
            windows_exe = [c for c in executables if c.suffix.lower() == ".exe"]
            return str(windows_exe[0]) if windows_exe else str(executables[0])
        return str(executables[0])
    for name in ("stockfish", "stockfish.exe"):
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            candidate = Path(directory) / name
            if candidate.is_file():
                return str(candidate)
    return None


class EngineNotFoundError(RuntimeError):
    pass

class MoveProvider:
    def is_automatic(self) -> bool:
        return False

    def get_move(self) -> str:
        raise NotImplementedError

    def compute_move(self, board: chess.Board) -> str:
        raise NotImplementedError

    def pop_move(self) -> str:
        raise NotImplementedError

    def close(self) -> None:
        pass


class HumanMoveProvider(MoveProvider):
    pass


class ComputerMoveProvider(MoveProvider):
    def __init__(self, elo_strength: int = DEFAULT_ELO,
                 time_to_think_in_sec: float = 1.0,
                 engine_path: str | None = None):
        engine_path = engine_path or find_stockfish()
        if engine_path is None:
            raise EngineNotFoundError(
                "Stockfish not found in gameplay/game_logic/stockfish or on PATH.")
        self.elo = elo_strength
        self.time_to_think_in_sec = time_to_think_in_sec
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path, creationflags=subprocess.CREATE_NO_WINDOW,)
        self.engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": elo_strength,
        })
        self.next_move: str | None = None

    @override
    def is_automatic(self) -> bool:
        return True

    @override
    def compute_move(self, board: chess.Board) -> str:
        """create next move but not execute it, only remmber and return"""
        limit = chess.engine.Limit(time=self.time_to_think_in_sec)
        result = self.engine.play(board, limit)
        assert result.move is not None
        self.next_move = result.move.uci()
        return self.next_move

    @override
    def pop_move(self) -> str:
        """Return the prepared move and clear it."""
        move = self.get_move()
        self.next_move = None
        return move

    @override
    def get_move(self) -> str:
        if self.next_move is None:
            raise RuntimeError("Move has not been prepared.")
        return self.next_move

    @override
    def close(self) -> None:
        self.engine.quit()


class Game:
    def __init__(self, user_id: int | None = None,
                 white_provider: MoveProvider | None = None,
                 black_provider: MoveProvider | None = None):
        self.user_id = user_id
        self._move_white_provider = white_provider or HumanMoveProvider()
        self._move_black_provider = black_provider or HumanMoveProvider()
        self._board = chess.Board()
        self._san_history: list[str] = []

    @classmethod
    def move_to_positions(cls, move: str) -> tuple[str, str]:
        """Split a UCI move into source and destination squares."""
        return move[:SQUARE_CODE_SIZE], move[SQUARE_CODE_SIZE:2 * SQUARE_CODE_SIZE]

    @property
    def board(self) -> chess.Board:
        return self._board

    @property
    def fen(self) -> str:
        return self._board.fen()

    @property
    def current_player(self) -> Color:
        return to_color(self._board.turn)

    @property
    def actual_move_provider(self) -> MoveProvider:
        if self.current_player == WHITE:
            return self._move_white_provider
        return self._move_black_provider

    @property
    def move_history(self) -> list[str]:
        return list(self._san_history)

    @property
    def last_move(self) -> str | None:
        if not self._board.move_stack:
            return None
        return self._board.move_stack[-1].uci()

    def is_automatic_move(self) -> bool:
        return self.actual_move_provider.is_automatic()

    def compute_automatic_move(self) -> str:
        return self.actual_move_provider.compute_move(self._board)

    def execute_automatic_move(self) -> str:
        move = self.actual_move_provider.pop_move()
        assert self.make_move(move)
        return move

    def board_to_display(self) -> BoardFormat:
        result: BoardFormat = {}
        for square in chess.SQUARES:
            piece = self._board.piece_at(square)
            if piece is not None:
                result[chess.square_name(square)] = (
                    _to_piece_type(piece), to_color(piece.color))
        return result

    def status(self) -> str:
        if self._board.is_checkmate():
            return CHECKMATE_STATUS
        if self._board.is_stalemate():
            return STALEMATE_STATUS
        if (self._board.is_insufficient_material()
                or self._board.is_seventyfive_moves()
                or self._board.is_fivefold_repetition()):
            return DRAW_STATUS
        if self._board.is_check():
            return CHECK_STATUS
        return NORMAL_STATUS

    def is_game_over(self) -> bool:
        return self.status() in (CHECKMATE_STATUS, STALEMATE_STATUS, DRAW_STATUS)

    def winner(self) -> Color | None:
        if self._board.is_checkmate():
            return opposite(self.current_player)
        return None

    def position_legal_from(self, position_start: Square) -> list[Square]:
        start_square = chess.parse_square(position_start)
        targets: list[Square] = []
        for move in self._board.legal_moves:
            if move.from_square == start_square:
                targets.append(chess.square_name(move.to_square))
        return targets

    def needs_promotion(self, position_start: Square, position_end: Square) -> bool:
        """if this move leads to promotion"""
        start = chess.parse_square(position_start)
        end = chess.parse_square(position_end)
        piece = self._board.piece_at(start)
        if piece is None or piece.piece_type != chess.PAWN:
            return False
        return chess.square_rank(end) in (0, 7)

    def make_move_between(self, position_start: Square, position_end: Square,
                          promotion: str | None = None) -> bool:
        code = position_start + position_end
        if promotion is not None:
            code += promotion.lower()
        return self.make_move(code)

    def make_move(self, move_code: str) -> bool:
        try:
            move = chess.Move.from_uci(move_code)
        except ValueError:
            return False
        if move not in self._board.legal_moves:
            return False
        san = self._board.san(move)
        self._board.push(move)
        self._san_history.append(san)
        return True

    def load_fen(self, fen: str) -> None:
        """Load the board from a FEN string."""
        self._board.set_fen(fen)
        self._san_history = []

    def reset(self) -> None:
        self._board.reset()
        self._san_history = []

    def load_all_games(self) -> list[tuple]:
        """Return a list of the user's saved games."""
        if self.user_id is None:
            return []
        return database.load_all_games(self.user_id)

    def to_pgn(self) -> str:
        """Return the current game in PGN format."""
        game = chess.pgn.Game()
        node: chess.pgn.GameNode = game
        for move in self._board.move_stack:
            node = node.add_variation(move)
        game.headers["Result"] = self._board.result()
        return str(game)
        
    def save_game(self) -> int:
        if self.user_id is None:
            raise ValueError("Write requires log in user.")
        return database.save_game(self.user_id, self.to_pgn())

    def load_game(self, game_id: int) -> None:
        if self.user_id is None:
            raise ValueError("Load requires log in user.")
        pgn = database.load_game(self.user_id, game_id)
        if pgn is None:
            raise ValueError("Game not found.")

        self.load_pgn(pgn)

    def load_pgn(self, pgn: str) -> None:
        """Load a game from a PGN string."""
        parsed = chess.pgn.read_game(StringIO(pgn))
        if parsed is None:
            raise ValueError("Invalid PGN.")
        self._board = parsed.board()
        self._san_history = []
        for move in parsed.mainline_moves():
            san = self._board.san(move)
            self._board.push(move)
            self._san_history.append(san)

    def close(self) -> None:
        self._move_white_provider.close()
        self._move_black_provider.close()
