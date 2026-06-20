import tkinter as tk

import chess

from ..game_logic import game


PIECE_UNICODE = {
    "K": "♔", "Q": "♕", "R": "♖",
    "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜",
    "b": "♝", "n": "♞", "p": "♟",
}

LIGHT_COLOR = "#f0d9b5"
DARK_COLOR = "#b58863"
SELECTED_COLOR = "#f6f669"
TARGET_COLOR = "#aacc66"
LAST_MOVE_COLOR = "#cdd26a"
PIECE_FG = "#202020"

PROMOTION_LABELS = (("Q", "Hetman"), ("R", "Wieża"), ("B", "Goniec"), ("N", "Skoczek"))


class BoardView(tk.Frame):
    def __init__(self, master, on_move, square_size: int = 64):
        super().__init__(master)
        self._on_move = on_move
        self._board = chess.Board()
        self._orientation = game.WHITE
        self._interactive: set[str] = {game.WHITE, game.BLACK}
        self._enabled = True
        self._selected: str | None = None
        self._targets: list[str] = []
        self._last_move: tuple[str, str] | None = None
        self._buttons: dict[tuple[int, int], tk.Button] = {}
        self._build(square_size)
        self.refresh()

    def _build(self, square_size: int) -> None:
        pixels = max(1, square_size // 16)
        for row in range(game.BOARD_SIZE):
            for col in range(game.BOARD_SIZE):
                button = tk.Button(
                    self,
                    text="",
                    width=2,
                    font=("Segoe UI Symbol", square_size // 2),
                    fg=PIECE_FG,
                    relief="flat",
                    borderwidth=0,
                    padx=pixels,
                    pady=pixels,
                    command=lambda r=row, c=col: self._on_cell_click(r, c),
                )
                button.grid(row=row, column=col, sticky="nsew")
                self._buttons[(row, col)] = button

    def set_fen(self, fen: str) -> None:
        self._board.set_fen(fen)
        self._selected = None
        self._targets = []
        self.refresh()

    def set_orientation(self, color: str) -> None:
        self._orientation = color
        self.refresh()

    def set_interactive(self, colors: set[str]) -> None:
        self._interactive = set(colors)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_last_move(self, last_move_uci: str | None) -> None:
        if last_move_uci:
            self._last_move = game.Game.move_to_positions(last_move_uci)
        else:
            self._last_move = None

    def _cell_to_square(self, row: int, col: int) -> str:
        if self._orientation == game.WHITE:
            file_index = col
            rank_index = game.BOARD_SIZE - 1 - row
        else:
            file_index = game.BOARD_SIZE - 1 - col
            rank_index = row
        return chess.square_name(chess.square(file_index, rank_index))

    def _on_cell_click(self, row: int, col: int) -> None:
        if not self._enabled:
            return
        square = self._cell_to_square(row, col)
        current = game.to_color(self._board.turn)
        if current not in self._interactive:
            return
        piece = self._board.piece_at(chess.parse_square(square))
        if self._selected is None:
            if piece is not None and game.to_color(piece.color) == current:
                self._selected = square
                self._targets = self._legal_from(square)
                self.refresh()
            return
        if square == self._selected:
            self._clear_selection()
            self.refresh()
            return
        if piece is not None and game.to_color(piece.color) == current:
            self._selected = square
            self._targets = self._legal_from(square)
            self.refresh()
            return
        if square in self._targets:
            promotion = self._maybe_promotion(self._selected, square)
            origin = self._selected
            self._clear_selection()
            self.refresh()
            self._on_move(origin, square, promotion)

    def _legal_from(self, square: str) -> list[str]:
        start = chess.parse_square(square)
        return [chess.square_name(move.to_square)
                for move in self._board.legal_moves
                if move.from_square == start]

    def _maybe_promotion(self, origin: str, target: str) -> str | None:
        piece = self._board.piece_at(chess.parse_square(origin))
        if piece is None or piece.piece_type != chess.PAWN:
            return None
        if chess.square_rank(chess.parse_square(target)) not in (0, 7):
            return None
        return self._ask_promotion()

    def _ask_promotion(self) -> str:
        dialog = tk.Toplevel(self)
        dialog.title("Promocja pionka")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        choice = {"value": "q"}

        def pick(letter: str) -> None:
            choice["value"] = letter.lower()
            dialog.destroy()

        tk.Label(dialog, text="Wybierz figurę:", font=("Segoe UI", 11),
                 padx=12, pady=8).pack()
        row = tk.Frame(dialog)
        row.pack(padx=12, pady=8)
        for letter, name in PROMOTION_LABELS:
            tk.Button(row, text=f"{PIECE_UNICODE[letter]} {name}",
                      font=("Segoe UI Symbol", 12), width=10,
                      command=lambda l=letter: pick(l)).pack(side="left", padx=4)
        dialog.protocol("WM_DELETE_WINDOW", lambda: pick("Q"))
        dialog.grab_set()
        self.wait_window(dialog)
        return choice["value"]

    def _clear_selection(self) -> None:
        self._selected = None
        self._targets = []

    def refresh(self) -> None:
        check_square = None
        if self._board.is_check():
            king = self._board.king(self._board.turn)
            if king is not None:
                check_square = chess.square_name(king)
        for (row, col), button in self._buttons.items():
            square = self._cell_to_square(row, col)
            piece = self._board.piece_at(chess.parse_square(square))
            button.configure(text=PIECE_UNICODE[piece.symbol()] if piece else "")
            file_index = chess.square_file(chess.parse_square(square))
            rank_index = chess.square_rank(chess.parse_square(square))
            base = LIGHT_COLOR if (file_index + rank_index) % 2 == 1 else DARK_COLOR
            if square == self._selected:
                background = SELECTED_COLOR
            elif square in self._targets:
                background = TARGET_COLOR
            elif square == check_square:
                background = "#e57373"
            elif self._last_move and square in self._last_move:
                background = LAST_MOVE_COLOR
            else:
                background = base
            button.configure(bg=background, activebackground=background)
