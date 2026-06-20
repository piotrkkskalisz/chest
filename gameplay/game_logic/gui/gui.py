import importlib.util
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from gameplay.game_logic import game


WHITE = game.WHITE
BLACK = game.BLACK
NORMAL_STATUS = game.NORMAL_STATUS
CHECK_STATUS = game.CHECK_STATUS
CHECKMATE_STATUS = game.CHECKMATE_STATUS
STALEMATE_STATUS = game.STALEMATE_STATUS

BOARD_SIZE = 8
FILES = "abcdefgh"

PIECE_SYMBOLS = {
    ("P", WHITE): "♙",
    ("N", WHITE): "♘",
    ("B", WHITE): "♗",
    ("R", WHITE): "♖",
    ("Q", WHITE): "♕",
    ("K", WHITE): "♔",
    ("P", BLACK): "♟",
    ("N", BLACK): "♞",
    ("B", BLACK): "♝",
    ("R", BLACK): "♜",
    ("Q", BLACK): "♛",
    ("K", BLACK): "♚",
}

LIGHT_COLOR = "#f0d9b5"
DARK_COLOR = "#b58863"
SELECTED_COLOR = "#f6f669"
TARGET_COLOR = "#aacc66"
PIECE_FG = "#202020"

COLOR_NAMES = {WHITE: "Białe", BLACK: "Czarne"}
MIN_TIME = 1
TIME_TO_DISPLAY_MOVE_MILSEC = 2_000

class ChessGUI(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("Szachy")
        self.master.resizable(False, False)
        
        self.game = game.Game()
        self._reset_selection()
        self.buttons = {}

        self._build_status_bar()
        self._build_board()
        self._build_controls()
        self._refresh()

    def _build_status_bar(self):
        self.status_var = tk.StringVar()
        label = tk.Label(self, textvariable=self.status_var, font=("Segoe UI", 14, "bold"), pady=8)
        label.grid(row=0, column=0, columnspan=BOARD_SIZE, sticky="ew")

    def _build_board(self):
        board_frame = tk.Frame(self)
        board_frame.grid(row=1, column=0, columnspan=BOARD_SIZE)

        for display_row in range(BOARD_SIZE):
            for display_col in range(BOARD_SIZE):
                square = self._square_name(display_row, display_col)
                button = tk.Button(
                    board_frame,
                    text="",
                    width=3,
                    height=1,
                    font=("Segoe UI Symbol", 28),
                    fg=PIECE_FG,
                    relief="flat",
                    borderwidth=0,
                    command=lambda sq=square: self._on_square_click(sq),
                )
                button.grid(row=display_row, column=display_col)
                self.buttons[square] = button
                                                        
    def _build_controls(self):
        controls = tk.Frame(self)
        controls.grid(row=2, column=0, columnspan=BOARD_SIZE, pady=8)

        new_game_button = tk.Button(controls, text="Nowa gra", font=("Segoe UI", 11), command=self._new_game)
        new_game_button.pack()

    def _square_name(self, display_row, display_col):       
        file_char = FILES[display_col]                              
        rank = BOARD_SIZE - display_row                     
        return f"{file_char}{rank}"                         

    def _square_is_light(self, square):
        file_index = FILES.index(square[0])
        rank = int(square[1])
        return (file_index + rank) % 2 == 0

    def _new_game(self):
        self.game = game.Game()
        self._reset_selection()
        self._refresh()

    def _on_square_click(self, square):
        board = self.game.board_to_display()
        current = self.game.current_player

        if self.selected_square is None:
            piece = board.get(square)
            if piece is not None and piece[1] == current:
                self.selected_square = square
                self.legal_targets = self.game.position_legal_from(square)
            self._refresh()
            return

        if square == self.selected_square:
            self._reset_selection()
            self._refresh()
            return

        piece = board.get(square)
        if piece is not None and piece[1] == current:
            self.selected_square = square
            self.legal_targets = self.game.position_legal_from(square)
            self._refresh()
            return

        moved = self.game.make_move_between(self.selected_square, square)
        if moved:
            self._reset_selection()
            self._refresh()
            self.after(MIN_TIME, self._after_move)
    
    def _after_move(self):
        #logic
        if self._announce_end():
            return
        if not self.game.is_automatic_move():
            return
        move = self.game.compute_automatic_move()
        self._display_move(move)
        
    def _display_move(self, move):
        start, end = game.Game.move_to_positions(move)
        self.selected_square = start
        self.legal_targets = [end]
        self._refresh()
        self.after(TIME_TO_DISPLAY_MOVE_MILSEC, self._finish_display_move)

    def _finish_display_move(self):
        self.game.execute_automate_move()
        self._reset_selection()
        self._refresh()
        self._after_move()

    def _reset_selection(self):
        self.selected_square = None
        self.legal_targets = []

    def _refresh(self):
        board = self.game.board_to_display()

        for square, button in self.buttons.items():
            piece = board.get(square)
            symbol = PIECE_SYMBOLS[piece] if piece is not None else ""
            button.configure(text=symbol)

            if square == self.selected_square:
                background = SELECTED_COLOR
            elif square in self.legal_targets:
                background = TARGET_COLOR
            else:
                background = LIGHT_COLOR if self._square_is_light(square) else DARK_COLOR

            button.configure(bg=background, activebackground=background)

        self._refresh_status()

    def _refresh_status(self):
        status = self.game.status()
        player = COLOR_NAMES[self.game.current_player]

        if status == CHECKMATE_STATUS:
            winner = COLOR_NAMES[WHITE] if self.game.current_player == BLACK else COLOR_NAMES[BLACK]
            self.status_var.set(f"Szach-mat! Wygrywają {winner}.")
        elif status == STALEMATE_STATUS:
            self.status_var.set("Pat! Remis.")
        elif status == CHECK_STATUS:
            self.status_var.set(f"Szach! Ruch: {player}")
        else:
            self.status_var.set(f"Ruch: {player}")

    def _announce_end(self):
        status = self.game.status()
        if status == CHECKMATE_STATUS:
            winner = COLOR_NAMES[WHITE] if self.game.current_player == BLACK else COLOR_NAMES[BLACK]
            messagebox.showinfo("Koniec gry", f"Szach-mat! Wygrywają {winner}.")
            return True
        elif status == STALEMATE_STATUS:
            messagebox.showinfo("Koniec gry", "Pat! Remis.")
            return True
        return False

def main():
    root = tk.Tk()
    app = ChessGUI(root)
    app.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
