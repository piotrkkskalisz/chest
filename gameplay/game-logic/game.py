import chess

from typing import Literal

BOARD_SIZE = 8

WHITE = "white"
BLACK = "black"

NORMAL_STATUS = "normal"
CHECK_STATUS = "check"
CHECKMATE_STATUS = "checkmate"
STALEMATE_STATUS = "stalemate"

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

class Game:
    def __init__(self):
        self._board = chess.Board()

    def current_player(self) -> Color:
        return to_color(self._board.turn)

    
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


    
    def make_move(self, position_start: Square, position_end: Square) -> bool:
        """Performs move and returns whether it succeeded."""
        move = chess.Move.from_uci(position_start+position_end)

        if move not in self._board.legal_moves:
            return False

        self._board.push(move)
        return True
    
#TODO:
# Promotion handling.