import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import simpledialog

from tkinter import messagebox


from ..game_logic import game
from ..network import protocol
from ..network.client import NetworkClient
from ..network.server import GameServer, local_ip_address
from .board_view import BoardView
from .. import auth

COLOR_NAMES = {game.WHITE: "Białe", game.BLACK: "Czarne"}
ENGINE_POLL_MS = 100
NETWORK_POLL_MS = 100
TITLE_FONT = ("Segoe UI", 22, "bold")
BUTTON_FONT = ("Segoe UI", 13)
STATUS_FONT = ("Segoe UI", 14, "bold")


def status_text(status: str, turn: str, winner: str | None) -> str:
    if status == game.CHECKMATE_STATUS:
        champion = winner or game.opposite(turn)
        return f"Szach-mat! Wygrywają {COLOR_NAMES[champion]}."
    if status == game.STALEMATE_STATUS:
        return "Pat! Remis."
    if status == game.DRAW_STATUS:
        return "Remis."
    if status == game.CHECK_STATUS:
        return f"Szach! Ruch: {COLOR_NAMES[turn]}"
    return f"Ruch: {COLOR_NAMES[turn]}"

class LoginScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        tk.Label(self, text=" Szachy", font=TITLE_FONT, pady=20).pack()
        tk.Label(self, text="Logowanie", font=("Segoe UI", 16, "bold")).pack(pady=10)

        tk.Label(self, text="Login:", font=BUTTON_FONT).pack()
        self.username_entry = tk.Entry(self, font=("Segoe UI", 12), width=24)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Hasło:", font=BUTTON_FONT).pack()
        self.password_entry = tk.Entry(
            self,
            font=("Segoe UI", 12),
            show="*",
            width=24
        )
        self.password_entry.pack(pady=5)

        tk.Button(
            self,
            text="Zaloguj",
            font=BUTTON_FONT,
            width=20,
            command= self.login
        ).pack(pady=12)

        tk.Button(
            self,
            text="Załóż konto",
            font=("Segoe UI", 11),
            command= self.app.show_register
        ).pack()

    def login(self):
        user_id = auth.login(self.username_entry.get().strip(),self.password_entry.get()) 
        if user_id is None:
            self.failure_login()

        else:
            self.app.set_user(user_id)
            self.app.show_menu()

    def failure_login(self):
        messagebox.showerror(
            "Logowanie",
            "Nieprawidłowy login lub hasło."
        )

        self.password_entry.delete(0, tk.END)
        self.password_entry.focus_set()        


class RegisterScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        tk.Label(self, text="Szachy", font=TITLE_FONT, pady=20).pack()
        tk.Label(self, text="Rejestracja", font=("Segoe UI", 16, "bold")).pack(pady=10)

        tk.Label(self, text="Login:", font=BUTTON_FONT).pack()
        self.username_entry = tk.Entry(self, font=("Segoe UI", 12), width=24)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Hasło:", font=BUTTON_FONT).pack()
        self.password_entry = tk.Entry(
            self,
            font=("Segoe UI", 12),
            show="*",
            width=24
        )
        self.password_entry.pack(pady=5)

        tk.Label(self, text="Powtórz hasło:", font=BUTTON_FONT).pack()
        self.repeat_password_entry = tk.Entry(
            self,
            font=("Segoe UI", 12),
            show="*",
            width=24
        )
        self.repeat_password_entry.pack(pady=5)

        tk.Button(
            self,
            text="Załóż konto",
            font=BUTTON_FONT,
            width=20,
            command=self.register
        ).pack(pady=12)

        tk.Button(
            self,
            text="Powrót do logowania",
            font=("Segoe UI", 11),
            command=self.app.show_login
        ).pack()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        repeat_password = self.repeat_password_entry.get()

        if password != repeat_password:
            self.failure_register("Hasła nie są identyczne.")
            return

        user_id = auth.register(username, password)

        if user_id is None:
            self.failure_register("Użytkownik o tej nazwie już istnieje.")
            return

        self.app.set_user(user_id)
        self.app.show_menu()

    def failure_register(self, message: str):
        messagebox.showerror("Rejestracja", message)

        self.password_entry.delete(0, tk.END)
        self.repeat_password_entry.delete(0, tk.END)
        self.password_entry.focus_set()

class MenuScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="♛  Szachy", font=TITLE_FONT, pady=24).pack()
        options = (
            ("Gra lokalna (dwie osoby)", self.app.show_local_game),
            ("Gra z komputerem", self.app.show_computer_setup),
            ("Gra w sieci LAN", self.app.show_network_setup),
            ("Wyjście", self.app.quit_app),
        )
        for text, command in options:
            tk.Button(self, text=text, font=BUTTON_FONT, width=26, pady=8,
                      command=command).pack(pady=6)
        tk.Label(self, text="", pady=12).pack()


class BaseGameScreen(tk.Frame):
    def __init__(self, master, app, title: str):
        super().__init__(master)
        self.app = app
        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, font=STATUS_FONT,
                 pady=8).grid(row=0, column=0, columnspan=2, sticky="ew")
        self.board_view = BoardView(self, self.handle_user_move)
        self.board_view.grid(row=1, column=0, padx=12, pady=12)
        self._build_side_panel(title)

    def _build_side_panel(self, title: str) -> None:
        panel = tk.Frame(self)
        panel.grid(row=1, column=1, sticky="ns", padx=12, pady=12)
        tk.Label(panel, text=title, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        list_frame = tk.Frame(panel)
        list_frame.pack(fill="both", expand=True, pady=8)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.history_list = tk.Listbox(list_frame, width=22, height=16,
                                       font=("Consolas", 11),
                                       yscrollcommand=scrollbar.set)
        self.history_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_list.yview)
        self.controls = tk.Frame(panel)
        self.controls.pack(fill="x", pady=8)
        tk.Button(panel, text="Menu główne", font=("Segoe UI", 11),
                  command=self.app.show_menu).pack(fill="x", pady=4)

    def _build_controls(self) -> None:
        pass

    def handle_user_move(self, origin: str, target: str, promotion: str | None) -> None:
        raise NotImplementedError

    def refresh_history(self, history: list[str]) -> None:
        self.history_list.delete(0, tk.END)
        for index in range(0, len(history), 2):
            number = index // 2 + 1
            white = history[index]
            black = history[index + 1] if index + 1 < len(history) else ""
            self.history_list.insert(tk.END, f"{number:>2}. {white:<7} {black}")
        self.history_list.see(tk.END)

    def cleanup(self) -> None:
        pass


class LocalGameScreen(BaseGameScreen):
    def __init__(self, master, app):
        super().__init__(master, app, "Historia ruchów")
        self.game = game.Game(app.user_id)
        self._build_controls()
        self.board_view.set_interactive({game.WHITE, game.BLACK})
        self._refresh()

    def _build_controls(self) -> None:
        tk.Button(self.controls, text="Nowa gra", font=("Segoe UI", 11),
                  command=self._new_game).pack(fill="x", pady=2)
        tk.Button(self.controls, text="Zapisz partię", font=("Segoe UI", 11),
                  command=self.game.save_game).pack(fill="x", pady=2)
        tk.Button(self.controls, text="Wczytaj partię", font=("Segoe UI", 11),
                  command=self.choose_game_to_load).pack(fill="x", pady=2)

    def choose_game_to_load(self):
        games = self.game.load_all_games()

        if not games:
            messagebox.showinfo("Informacja", "Brak zapisanych gier.")
            return
        """
        game_id = simpledialog.askinteger("Wczytaj grę",f"Dostępne gry:\n{games}\n\nPodaj ID gry:")

        if game_id is None:
            return

        self.game.load_game(game_id)
        """

        dialog = LoadGameDialog(self, games)
        dialog.grab_set()
        dialog.wait_window()

        if dialog.selected_game is None:
            return

        self.game.load_game(dialog.selected_game)

        self._refresh()


    def _new_game(self) -> None:
        self.game.reset()
        self._refresh()

    def handle_user_move(self, origin: str, target: str, promotion: str | None) -> None:
        if self.game.make_move_between(origin, target, promotion):
            self._refresh()
            self._announce_end()

    def _refresh(self) -> None:
        self.board_view.set_fen(self.game.fen)
        self.board_view.set_last_move(self.game.last_move)
        self.board_view.refresh()
        self.refresh_history(self.game.move_history)
        self.status_var.set(status_text(self.game.status(),
                                         self.game.current_player,
                                         self.game.winner()))

    def _announce_end(self) -> None:
        if self.game.is_game_over():
            messagebox.showinfo("Koniec gry",
                                status_text(self.game.status(),
                                            self.game.current_player,
                                            self.game.winner()))

    def _save(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".pgn",
                                            initialdir="saves",
                                            filetypes=[("PGN", "*.pgn")])
        if path:
            self.game.save_pgn(path)

    def _load(self) -> None:
        path = filedialog.askopenfilename(initialdir="saves",
                                          filetypes=[("PGN", "*.pgn")])
        if path:
            try:
                self.game.load_pgn(path)
                self._refresh()
            except (ValueError, OSError) as error:
                messagebox.showerror("Błąd", str(error))


class ComputerGameScreen(BaseGameScreen):
    def __init__(self, master, app, human_color: str, provider: game.ComputerMoveProvider):
        super().__init__(master, app, "Historia ruchów")
        self.human_color = human_color
        if human_color == game.WHITE:
            self.game = game.Game(app.user_id,  black_provider=provider)
        else:
            self.game = game.Game(app.user_id, white_provider=provider)
        self._build_controls()

        self._engine_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.board_view.set_orientation(human_color)
        self.board_view.set_interactive({human_color})
        self._refresh()
        self._maybe_engine_move()

    def _build_controls(self) -> None:
        tk.Button(self.controls, text="Nowa gra", font=("Segoe UI", 11),
                  command=self._new_game).pack(fill="x", pady=2)

    def _new_game(self) -> None:
        self.game.reset()
        self._refresh()
        self._maybe_engine_move()

    def handle_user_move(self, origin: str, target: str, promotion: str | None) -> None:
        if self.game.make_move_between(origin, target, promotion):
            self._refresh()
            if self.game.is_game_over():
                self._announce_end()
                return
            self._maybe_engine_move()

    def _maybe_engine_move(self) -> None:
        if self.game.is_game_over() or not self.game.is_automatic_move():
            return
        self.board_view.set_enabled(False)
        self.status_var.set("Komputer myśli...")
        threading.Thread(target=self._engine_worker, daemon=True).start()
        self.after(ENGINE_POLL_MS, self._poll_engine)

    def _engine_worker(self) -> None:
        try:
            self.game.compute_automatic_move()
            self._engine_queue.put(("ok", ""))
        except Exception as error:
            self._engine_queue.put(("error", str(error)))

    def _poll_engine(self) -> None:
        try:
            outcome, detail = self._engine_queue.get_nowait()
        except queue.Empty:
            self.after(ENGINE_POLL_MS, self._poll_engine)
            return
        self.board_view.set_enabled(True)
        if outcome == "error":
            messagebox.showerror("Silnik", detail)
            return
        self.game.execute_automatic_move()
        self._refresh()
        self._announce_end()

    def _refresh(self) -> None:
        self.board_view.set_fen(self.game.fen)
        self.board_view.set_last_move(self.game.last_move)
        self.board_view.refresh()
        self.refresh_history(self.game.move_history)
        self.status_var.set(status_text(self.game.status(),
                                         self.game.current_player,
                                         self.game.winner()))

    def _announce_end(self) -> None:
        if self.game.is_game_over():
            messagebox.showinfo("Koniec gry",
                                status_text(self.game.status(),
                                            self.game.current_player,
                                            self.game.winner()))

    def cleanup(self) -> None:
        try:
            self.game.close()
        except Exception:
            pass


class NetworkGameScreen(BaseGameScreen):
    def __init__(self, master, app, client: NetworkClient, server: GameServer | None):
        super().__init__(master, app, "Historia ruchów")
        self.client = client
        self.server = server
        self.my_color: str | None = None
        self.turn = game.WHITE
        self.finished = False
        self._build_controls()

        self.board_view.set_interactive(set())
        self.status_var.set("Oczekiwanie na połączenie...")
        self.after(NETWORK_POLL_MS, self._poll_network)

    def _build_controls(self) -> None:
        tk.Button(self.controls, text="Poddaj się", font=("Segoe UI", 11),
                  command=self._resign).pack(fill="x", pady=2)

    def _resign(self) -> None:
        if not self.finished:
            self.client.send_resign()

    def handle_user_move(self, origin: str, target: str, promotion: str | None) -> None:
        if self.finished or self.my_color is None:
            return
        self.board_view.set_enabled(False)
        self.client.send_move(origin, target, promotion)

    def _poll_network(self) -> None:
        while True:
            try:
                message = self.client.inbox.get_nowait()
            except queue.Empty:
                break
            self._handle_message(message)
        self.after(NETWORK_POLL_MS, self._poll_network)

    def _handle_message(self, message: dict) -> None:
        kind = message.get("type")
        if kind == protocol.TYPE_ASSIGNED:
            self._handle_assigned(message)
        elif kind == protocol.TYPE_STATE:
            self._handle_state(message)
        elif kind == protocol.TYPE_ILLEGAL:
            self.board_view.set_enabled(True)
            self.status_var.set("Nieprawidłowy ruch.")
        elif kind == protocol.TYPE_GAME_OVER:
            self._handle_game_over(message)
        elif kind == protocol.TYPE_ERROR:
            messagebox.showerror("Sieć", message.get("message", "Błąd połączenia."))
            self.status_var.set("Rozłączono.")
            self.board_view.set_enabled(False)

    def _handle_assigned(self, message: dict) -> None:
        self.my_color = message.get("color")
        if self.my_color in (game.WHITE, game.BLACK):
            self.board_view.set_orientation(self.my_color)
            self.board_view.set_interactive({self.my_color})
            self.status_var.set(f"Grasz: {COLOR_NAMES[self.my_color]}")
        else:
            self.status_var.set("Tryb obserwatora.")

    def _handle_state(self, message: dict) -> None:
        self.turn = message.get("turn", game.WHITE)
        self.board_view.set_fen(message["fen"])
        self.board_view.set_last_move(message.get("last_move"))
        self.board_view.refresh()
        self.refresh_history(message.get("history", []))
        self.board_view.set_enabled(self.turn == self.my_color and not self.finished)
        self.status_var.set(status_text(message.get("status", game.NORMAL_STATUS),
                                        self.turn, message.get("winner")))

    def _handle_game_over(self, message: dict) -> None:
        self.finished = True
        self.board_view.set_enabled(False)
        reason = message.get("reason")
        winner = message.get("winner")
        if reason == "resign" and winner:
            text = f"Przeciwnik się poddał. Wygrywają {COLOR_NAMES[winner]}."
        elif reason == "checkmate" and winner:
            text = f"Szach-mat! Wygrywają {COLOR_NAMES[winner]}."
        elif reason == "stalemate":
            text = "Pat! Remis."
        else:
            text = "Remis."
        self.status_var.set(text)
        messagebox.showinfo("Koniec gry", text)

    def cleanup(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass
        if self.server is not None:
            try:
                self.server.stop()
            except Exception:
                pass


class ComputerSetupScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="Gra z komputerem", font=TITLE_FONT, pady=20).pack()
        self.color_var = tk.StringVar(value=game.WHITE)
        self.elo_var = tk.IntVar(value=game.DEFAULT_ELO)
        self.time_var = tk.DoubleVar(value=1.0)

        color_frame = tk.Frame(self)
        color_frame.pack(pady=6)
        tk.Label(color_frame, text="Twój kolor:", font=BUTTON_FONT).pack(side="left", padx=6)
        tk.Radiobutton(color_frame, text="Białe", variable=self.color_var,
                       value=game.WHITE, font=BUTTON_FONT).pack(side="left")
        tk.Radiobutton(color_frame, text="Czarne", variable=self.color_var,
                       value=game.BLACK, font=BUTTON_FONT).pack(side="left")

        elo_frame = tk.Frame(self)
        elo_frame.pack(pady=6)
        tk.Label(elo_frame, text="Siła (ELO):", font=BUTTON_FONT).pack(side="left", padx=6)
        tk.Scale(elo_frame, from_=1320, to=2850, orient="horizontal", length=260,
                 variable=self.elo_var).pack(side="left")

        time_frame = tk.Frame(self)
        time_frame.pack(pady=6)
        tk.Label(time_frame, text="Czas na ruch (s):", font=BUTTON_FONT).pack(side="left", padx=6)
        tk.Scale(time_frame, from_=0.1, to=5.0, resolution=0.1, orient="horizontal",
                 length=260, variable=self.time_var).pack(side="left")

        tk.Button(self, text="Rozpocznij", font=BUTTON_FONT, width=20,
                  command=self._start).pack(pady=12)
        tk.Button(self, text="Powrót", font=("Segoe UI", 11),
                  command=self.app.show_menu).pack()

    def _start(self) -> None:
        try:
            provider = game.ComputerMoveProvider(self.elo_var.get(), self.time_var.get())
        except game.EngineNotFoundError as error:
            messagebox.showerror("Brak silnika", str(error))
            return
        self.app.show_computer_game(self.color_var.get(), provider)


class NetworkSetupScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        tk.Label(self, text="Gra w sieci LAN", font=TITLE_FONT, pady=20).pack()

        host_box = tk.LabelFrame(self, text="Załóż grę (host)", font=BUTTON_FONT, padx=12, pady=12)
        host_box.pack(fill="x", padx=20, pady=8)
        tk.Label(host_box, text=f"Twój adres IP: {local_ip_address()}",
                 font=("Consolas", 12)).pack(anchor="w")
        tk.Label(host_box, text=f"Port: {protocol.DEFAULT_PORT}",
                 font=("Consolas", 12)).pack(anchor="w")
        tk.Button(host_box, text="Uruchom hosta i graj (Białe)", font=BUTTON_FONT,
                  command=self._host).pack(pady=8)

        join_box = tk.LabelFrame(self, text="Dołącz do gry (klient)", font=BUTTON_FONT, padx=12, pady=12)
        join_box.pack(fill="x", padx=20, pady=8)
        row = tk.Frame(join_box)
        row.pack()
        tk.Label(row, text="Adres IP hosta:", font=BUTTON_FONT).pack(side="left", padx=4)
        self.ip_var = tk.StringVar(value="127.0.0.1")
        tk.Entry(row, textvariable=self.ip_var, font=("Consolas", 12), width=16).pack(side="left")
        tk.Label(row, text="Port:", font=BUTTON_FONT).pack(side="left", padx=4)
        self.port_var = tk.IntVar(value=protocol.DEFAULT_PORT)
        tk.Entry(row, textvariable=self.port_var, font=("Consolas", 12), width=7).pack(side="left")
        tk.Button(join_box, text="Połącz i graj (Czarne)", font=BUTTON_FONT,
                  command=self._join).pack(pady=8)

        tk.Button(self, text="Powrót", font=("Segoe UI", 11),
                  command=self.app.show_menu).pack(pady=8)

    def _host(self) -> None:
        server = GameServer(port=protocol.DEFAULT_PORT)
        try:
            port = server.start()
        except OSError as error:
            messagebox.showerror("Host", f"Nie można uruchomić serwera: {error}")
            return
        client = NetworkClient("127.0.0.1", port)
        try:
            client.connect()
        except OSError as error:
            server.stop()
            messagebox.showerror("Host", f"Błąd połączenia lokalnego: {error}")
            return
        self.app.show_network_game(client, server)

    def _join(self) -> None:
        client = NetworkClient(self.ip_var.get().strip(), self.port_var.get())
        try:
            client.connect()
        except OSError as error:
            messagebox.showerror("Połączenie", f"Nie można połączyć: {error}")
            return
        self.app.show_network_game(client, None)


class LoadGameDialog(tk.Toplevel):
    def __init__(self, master, games):
        super().__init__(master)

        self.title("Wczytaj grę")
        self.resizable(False, False)

        self.selected_game = None

        tk.Label(
            self,
            text="Wybierz zapisaną grę",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        container = tk.Frame(self)
        container.pack(padx=10, pady=10)

        for i, (game_id, date) in enumerate(games):

            card = tk.LabelFrame(
                container,
                text=f"Gra #{game_id}",
                padx=10,
                pady=10
            )

            row = i // 3
            column = i % 3

            card.grid(
                row=row,
                column=column,
                padx=8,
                pady=8,
                sticky="nsew"
            )

            tk.Label(
                card,
                text=date,
                font=("Segoe UI", 10)
            ).pack(pady=(0, 8))

            tk.Label(
                card,
                text="♟\nMiniatura\n(szachownica)",
                width=18,
                height=6,
                relief="solid"
            ).pack()

            tk.Button(
                card,
                text="Wybierz",
                command=lambda id=game_id: self._select(id)
            ).pack(fill="x", pady=(8, 0))

        tk.Button(
            self,
            text="Anuluj",
            command=self.destroy
        ).pack(pady=(0, 10))

    def _select(self, game_id):
        self.selected_game = game_id
        self.destroy()