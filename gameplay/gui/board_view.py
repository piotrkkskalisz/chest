import tkinter as tk

import chess

from ..game_logic import game
from . import theme


SOLID_GLYPH = {
    "p": "♟", "n": "♞", "b": "♝",
    "r": "♜", "q": "♛", "k": "♚",
}

PROMOTION_LABELS = (("Q", "Hetman"), ("R", "Wieza"), ("B", "Goniec"), ("N", "Skoczek"))

MIN_SQUARE = 40
MAX_SQUARE = 96


class BoardView(tk.Frame):

    def __init__(self, master, on_move, square_size: int = 72):
        super().__init__(master, bg=theme.BG)
        self._on_move = on_move
        self._board = chess.Board()
        self._orientation = game.WHITE
        self._interactive: set[str] = {game.WHITE, game.BLACK}
        self._enabled = True
        self._selected: str | None = None
        self._targets: list[str] = []
        self._last_move: tuple[str, str] | None = None

        self._square = square_size
        self._origin_x = 0
        self._origin_y = 0

        self.canvas = tk.Canvas(self, bg=theme.BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Configure>", self._on_resize)

        side = square_size * game.BOARD_SIZE
        self.canvas.configure(width=side, height=side)


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


    def _on_resize(self, event: tk.Event) -> None:
        usable = min(event.width, event.height)
        square = max(MIN_SQUARE, min(MAX_SQUARE, usable // game.BOARD_SIZE))
        self._square = square
        board_px = square * game.BOARD_SIZE
        self._origin_x = (event.width - board_px) // 2
        self._origin_y = (event.height - board_px) // 2
        self.refresh()


    def _cell_to_square(self, row: int, col: int) -> str:
        if self._orientation == game.WHITE:
            file_index = col
            rank_index = game.BOARD_SIZE - 1 - row
        else:
            file_index = game.BOARD_SIZE - 1 - col
            rank_index = row
        return chess.square_name(chess.square(file_index, rank_index))

    def _pixel_to_cell(self, x: int, y: int) -> tuple[int, int] | None:
        col = (x - self._origin_x) // self._square
        row = (y - self._origin_y) // self._square
        if 0 <= row < game.BOARD_SIZE and 0 <= col < game.BOARD_SIZE:
            return int(row), int(col)
        return None


    def _on_click(self, event: tk.Event) -> None:
        if not self._enabled:
            return
        cell = self._pixel_to_cell(event.x, event.y)
        if cell is None:
            return
        row, col = cell
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

    def _clear_selection(self) -> None:
        self._selected = None
        self._targets = []


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
        dialog.configure(bg=theme.SURFACE)
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        choice = {"value": "q"}

        def pick(letter: str) -> None:
            choice["value"] = letter.lower()
            dialog.destroy()

        theme.label(dialog, "Wybierz figure:", size=12, bg=theme.SURFACE).pack(
            padx=16, pady=(14, 8))
        row = tk.Frame(dialog, bg=theme.SURFACE)
        row.pack(padx=16, pady=(0, 14))
        for letter, name in PROMOTION_LABELS:
            glyph = SOLID_GLYPH[letter.lower()]
            theme.Button(row, text=glyph + "  " + name, kind="ghost",
                         command=lambda l=letter: pick(l)).pack(side="left", padx=4)
        dialog.protocol("WM_DELETE_WINDOW", lambda: pick("Q"))
        dialog.grab_set()
        self.wait_window(dialog)
        return choice["value"]


    def refresh(self) -> None:
        self.canvas.delete("all")
        check_square = None
        if self._board.is_check():
            king = self._board.king(self._board.turn)
            if king is not None:
                check_square = chess.square_name(king)

        size = self._square
        label_font = theme.ui_font(max(8, size // 7), bold=True)
        glyph_font = theme.piece_font(int(size * 0.74))

        for row in range(game.BOARD_SIZE):
            for col in range(game.BOARD_SIZE):
                square = self._cell_to_square(row, col)
                parsed = chess.parse_square(square)
                file_index = chess.square_file(parsed)
                rank_index = chess.square_rank(parsed)
                x0 = self._origin_x + col * size
                y0 = self._origin_y + row * size
                x1, y1 = x0 + size, y0 + size

                base = (theme.BOARD_LIGHT if (file_index + rank_index) % 2 == 1
                        else theme.BOARD_DARK)
                if square == self._selected:
                    fill = theme.SQ_SELECTED
                elif square == check_square:
                    fill = theme.SQ_CHECK
                elif self._last_move and square in self._last_move:
                    fill = theme.SQ_LAST
                else:
                    fill = base
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, width=0)

                label_color = (theme.BOARD_DARK if base == theme.BOARD_LIGHT
                               else theme.BOARD_LIGHT)
                if row == game.BOARD_SIZE - 1:
                    self.canvas.create_text(
                        x1 - size * 0.12, y1 - size * 0.12,
                        text=chess.FILE_NAMES[file_index], anchor="se",
                        fill=label_color, font=label_font)
                if col == 0:
                    self.canvas.create_text(
                        x0 + size * 0.10, y0 + size * 0.10,
                        text=chess.RANK_NAMES[rank_index], anchor="nw",
                        fill=label_color, font=label_font)

                piece = self._board.piece_at(parsed)
                cx, cy = x0 + size / 2, y0 + size / 2
                if square in self._targets:
                    self._draw_target(cx, cy, size, piece is not None)
                if piece is not None:
                    self._draw_piece(cx, cy, piece, glyph_font)

    def _draw_target(self, cx: float, cy: float, size: int, occupied: bool) -> None:
        if occupied:
            r = size * 0.46
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    outline=theme.SQ_TARGET, width=max(3, size // 16))
        else:
            r = size * 0.16
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    fill=theme.SQ_TARGET, outline="")

    def _draw_piece(self, cx: float, cy: float, piece: chess.Piece,
                    glyph_font: tuple) -> None:
        glyph = SOLID_GLYPH[piece.symbol().lower()]
        fill = theme.PIECE_LIGHT if piece.color == chess.WHITE else theme.PIECE_DARK
        offset = max(1, self._square // 40)
        for dx, dy in ((-offset, 0), (offset, 0), (0, -offset), (0, offset)):
            self.canvas.create_text(cx + dx, cy + dy, text=glyph,
                                    fill=theme.PIECE_OUTLINE, font=glyph_font)
        self.canvas.create_text(cx, cy, text=glyph, fill=fill, font=glyph_font)
