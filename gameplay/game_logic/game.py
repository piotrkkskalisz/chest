import chess
import chess.engine
from typing import override
from typing import Literal
from abc import ABC, abstractmethod


BOARD_SIZE = 8

WHITE = "white"
BLACK = "black"

NORMAL_STATUS = "normal"
CHECK_STATUS = "check"
CHECKMATE_STATUS = "checkmate"
STALEMATE_STATUS = "stalemate"

SQUARE_CODE_SIZE = 2

type PieceType = Literal["P", "N", "B", "R", "Q", "K"]

#type ROW = Literal['1', '2', '3', '4', '5', '6', '7', '8']
#type COLUMNS = Literal['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

type Square = str


def to_piece_type(piece: chess.Piece) -> PieceType:
    """Converts python-chess piece to piece symbol."""
    match piece.piece_type:
        case chess.PAWN:
            return "P"
        case chess.KNIGHT:
            return "N"
        case chess.BISHOP:
            return "B"
        case chess.ROOK:
            return "R"
        case chess.QUEEN:
            return "Q"
        case chess.KING:
            return "K"
        
    assert False, "unreachable"

type Color = Literal["white", "black"]

def to_color(color_bool: bool) -> Color:
    """Converts python-chess color format (bool) to Color format (string)."""
    return WHITE if color_bool else BLACK



type PieceDisplay = tuple[PieceType, Color]
type BoardFormat = dict[Square, PieceDisplay]

"""
    def __init__(self, type):
        self.type = type 
    
    type = "HUMAN"
    def __init__(self):
        super().__init__(type)
    """
class MoveProvider:
    def is_automatic(self) -> bool:
        return False
    
    def get_move(self) -> str:
        raise NotImplementedError("This move is manual")
    
    def compute_move(self, board: chess.Board) -> str:
        raise NotImplementedError("This move is manual")
        
    def pop_move(self):
        raise NotImplementedError("This move is manual")

    def close(self) -> None:
        pass


class HumanMoveProvider(MoveProvider):
    pass
    
class ComputerMoveProvider(MoveProvider):
    def __init__(self, elo_strength: int, time_to_think_in_sec: float = 1):
        self.elo = elo_strength
        self.time_to_think_in_sec = time_to_think_in_sec
        self.engine = chess.engine.SimpleEngine.popen_uci(
            r"gameplay\game_logic\stockfish\stockfish-windows-x86-64-avx2.exe")
        self.engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": elo_strength
        })
        self.next_move: str | None = None

    @override
    def is_automatic(self) -> bool:
        return True
    
    @override
    def compute_move(self, board: chess.Board) -> str:
        move = self.engine.play(board, chess.engine.Limit(time=self.time_to_think_in_sec)).move
        assert move is not None
        self.next_move = move.uci()
        return self.next_move 

    @override
    def pop_move(self):
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
    def __init__(self, white_provider: MoveProvider | None = None,
                black_provider: MoveProvider | None = None):
        self.move_white_provider = white_provider if white_provider is not None else HumanMoveProvider()
        self.move_black_provider = black_provider if black_provider is not None else ComputerMoveProvider(1320)
        self._board = chess.Board()
    #popzbyc sie magicznych liczb
    @classmethod
    def move_to_positions(cls, move: str) -> tuple[str, str]:
        return move[:SQUARE_CODE_SIZE], move[SQUARE_CODE_SIZE:2* SQUARE_CODE_SIZE]


    @property
    def current_player(self) -> Color:
        return to_color(self._board.turn)

    @property
    def actual_move_provider(self):
        return self.move_white_provider if self.current_player == WHITE else self.move_black_provider


    def is_automatic_move(self):
        return self.actual_move_provider.is_automatic()
    
    def compute_automatic_move(self) -> str:
        return self.actual_move_provider.compute_move(self._board)

    def execute_automate_move(self) -> str:
        move = self.actual_move_provider.pop_move()
        is_correct = self.make_move(move)
        assert is_correct
        return move

    def board_to_display(self) -> BoardFormat:
        """Returns board state with pieces and their colors."""
        board: BoardFormat = {}

        for square in chess.SQUARES:
            piece = self._board.piece_at(square)

            if piece is not None:
                board[chess.square_name(square)] = (to_piece_type(piece), to_color(piece.color))

        return board
    

    def status(self) -> str:
        """Returns current game status."""
        if self._board.is_checkmate():
            return CHECKMATE_STATUS

        if self._board.is_stalemate():
            return STALEMATE_STATUS

        if self._board.is_check():
            return CHECK_STATUS

        return NORMAL_STATUS
    
    def position_legal_from(self, position_start: Square) -> list[Square]:
        """Returns legal target positions from given position."""
        start_square = chess.parse_square(position_start)
        positions: list[Square] = []

        for move in self._board.legal_moves:
            if move.from_square == start_square:
                positions.append(chess.square_name(move.to_square))

        return positions
    
    def make_move_between(self, position_start: Square, position_end: Square) -> bool:
        return self.make_move(position_start+position_end)
    
    def make_move(self, move_code: str) -> bool:
        """Performs move and returns whether it succeeded."""
        move = chess.Move.from_uci(move_code)

        if move not in self._board.legal_moves:
            return False

        self._board.push(move)
        return True 


    def close(self):
        self.move_white_provider.close()
        self.move_black_provider.close()

#TODO:
# Promotion handling.