import queue
import threading
import tkinter as tk
from tkinter import messagebox

from ..game_logic import game
from ..network import protocol
from ..network.client import NetworkClient
from ..network.server import GameServer, local_ip_address
from .board_view import BoardView
from . import theme
from .. import auth

COLOR_NAMES = {game.WHITE: "Białe", game.BLACK: "Czarne"}
ENGINE_POLL_MS = 100
NETWORK_POLL_MS = 100


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


def _centered_card(screen: tk.Frame, pad_x: int = 36, pad_y: int = 28) -> tk.Frame:
    card = theme.card(screen)
    card.place(relx=0.5, rely=0.5, anchor="center")
    inner = tk.Frame(card, bg=theme.SURFACE)
    inner.pack(padx=pad_x, pady=pad_y)
    return inner


class LoginScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=theme.BG)
        self.app = app
        inner = _centered_card(self)

        theme.title(inner, "♛  Szachy", size=30).pack(pady=(0, 4))
        theme.subtitle(inner, "Logowanie").pack(pady=(0, 18))

        theme.label(inner, "Login:").pack(anchor="w")
        self.username_entry = theme.entry(inner, width=26)
        self.username_entry.pack(pady=(2, 12), ipady=4)

        theme.label(inner, "Hasło:").pack(anchor="w")
        self.password_entry = theme.entry(inner, show="*", width=26)
        self.password_entry.pack(pady=(2, 18), ipady=4)
        self.password_entry.bind("<Return>", lambda _e: self.login())

        theme.Button(inner, "Zaloguj", command=self.login).pack(fill="x")
        theme.Button(inner, "Załóż konto", kind="ghost",
                     command=self.app.show_register).pack(fill="x", pady=(10, 0))
        self.username_entry.focus_set()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Logowanie", "Podaj login i hasło.")
            return
        user_id = auth.login(username, password)
        if user_id is None:
            self.failure_login()
        else:
            self.app.set_user(user_id)
            self.app.show_menu()

    def failure_login(self):
        messagebox.showerror("Logowanie", "Nieprawidłowy login lub hasło.")
        self.password_entry.delete(0, tk.END)
        self.password_entry.focus_set()


class RegisterScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=theme.BG)
        self.app = app
        inner = _centered_card(self)

        theme.title(inner, "♛  Szachy", size=30).pack(pady=(0, 4))
        theme.subtitle(inner, "Rejestracja").pack(pady=(0, 18))

        theme.label(inner, "Login:").pack(anchor="w")
        self.username_entry = theme.entry(inner, width=26)
        self.username_entry.pack(pady=(2, 12), ipady=4)

        theme.label(inner, "Hasło:").pack(anchor="w")
        self.password_entry = theme.entry(inner, show="*", width=26)
        self.password_entry.pack(pady=(2, 12), ipady=4)

        theme.label(inner, "Powtórz hasło:").pack(anchor="w")
        self.repeat_password_entry = theme.entry(inner, show="*", width=26)
        self.repeat_password_entry.pack(pady=(2, 18), ipady=4)

        theme.Button(inner, "Załóż konto", command=self.register).pack(fill="x")
        theme.Button(inner, "Powrót do logowania", kind="ghost",
                     command=self.app.show_login).pack(fill="x", pady=(10, 0))
        self.username_entry.focus_set()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        repeat_password = self.repeat_password_entry.get()

        if not username or not password:
            self.failure_register("Podaj login i hasło.")
            return
        if len(password) < 4:
            self.failure_register("Hasło musi mieć co najmniej 4 znaki.")
            return
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
        super().__init__(master, bg=theme.BG)
        self.app = app
        inner = _centered_card(self, pad_x=48, pad_y=36)

        theme.title(inner, "♛  Szachy", size=34).pack(pady=(0, 6))
        theme.label(inner, "Wybierz tryb gry", muted=True).pack(pady=(0, 22))

        options = (
            ("Gra lokalna (dwie osoby)", self.app.show_local_game, "primary"),
            ("Gra z komputerem", self.app.show_computer_setup, "ghost"),
            ("Gra w sieci LAN", self.app.show_network_setup, "ghost"),
        )
        for text, command, kind in options:
            theme.Button(inner, text, command=command, kind=kind).pack(
                fill="x", pady=5, ipady=2)
        theme.Button(inner, "Wyjście", command=self.app.quit_app,
                     kind="danger").pack(fill="x", pady=(18, 0))


class BaseGameScreen(tk.Frame):
    def __init__(self, master, app, title: str):
        super().__init__(master, bg=theme.BG)
        self.app = app

        self.status_var = tk.StringVar(value="")
        status = tk.Label(self, textvariable=self.status_var,
                          font=theme.ui_font(15, bold=True), bg=theme.SURFACE,
                          fg=theme.TEXT, pady=12)
        status.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.board_view = BoardView(self, self.handle_user_move)
        self.board_view.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)


        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_side_panel(title)

    def _build_side_panel(self, title: str) -> None:
        panel = tk.Frame(self, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        panel.grid(row=1, column=1, sticky="ns", padx=(0, 16), pady=16)
        inner = tk.Frame(panel, bg=theme.SURFACE)
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        theme.subtitle(inner, title, size=13).pack(anchor="w")

        list_frame = tk.Frame(inner, bg=theme.SURFACE)
        list_frame.pack(fill="both", expand=True, pady=10)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.history_list = tk.Listbox(
            list_frame, width=24, height=18, font=theme.mono_font(11),
            bg=theme.SURFACE_LIGHT, fg=theme.TEXT, relief="flat",
            borderwidth=0, highlightthickness=0,
            selectbackground=theme.ACCENT, selectforeground=theme.TEXT_ON_ACCENT,
            yscrollcommand=scrollbar.set)
        self.history_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_list.yview)

        self.controls = tk.Frame(inner, bg=theme.SURFACE)
        self.controls.pack(fill="x", pady=8)

        theme.Button(inner, "Menu główne", kind="ghost",
                     command=self.app.show_menu).pack(fill="x", pady=(8, 0))

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
        theme.Button(self.controls, "Nowa gra", kind="ghost",
                     command=self._new_game).pack(fill="x", pady=3)
        theme.Button(self.controls, "Zapisz partię", kind="ghost",
                     command=self._save_to_db).pack(fill="x", pady=3)
        theme.Button(self.controls, "Wczytaj partię", kind="ghost",
                     command=self.choose_game_to_load).pack(fill="x", pady=3)

    def _save_to_db(self) -> None:
        try:
            self.game.save_game()
            messagebox.showinfo("Zapis", "Partia została zapisana.")
        except Exception as error:
            messagebox.showerror("Zapis", f"Nie udało się zapisać partii:\n{error}")

    def choose_game_to_load(self):
        games = self.game.load_all_games()
        if not games:
            messagebox.showinfo("Informacja", "Brak zapisanych gier.")
            return

        dialog = LoadGameDialog(self, games)
        dialog.grab_set()
        dialog.wait_window()

        if dialog.selected_game is None:
            return
        try:
            self.game.load_game(dialog.selected_game)
        except ValueError as error:
            messagebox.showerror("Wczytywanie", str(error))
            return
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


class ComputerGameScreen(BaseGameScreen):
    def __init__(self, master, app, human_color: str, provider):
        super().__init__(master, app, "Historia ruchów")
        self.human_color = human_color
        if human_color == game.WHITE:
            self.game = game.Game(app.user_id, black_provider=provider)
        else:
            self.game = game.Game(app.user_id, white_provider=provider)
        self._build_controls()

        self._engine_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.board_view.set_orientation(human_color)
        self.board_view.set_interactive({human_color})
        self._refresh()
        self._maybe_engine_move()

    def _build_controls(self) -> None:
        theme.Button(self.controls, "Nowa gra", kind="ghost",
                     command=self._new_game).pack(fill="x", pady=3)

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
        theme.Button(self.controls, "Poddaj się", kind="danger",
                     command=self._resign).pack(fill="x", pady=3)

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
        super().__init__(master, bg=theme.BG)
        self.app = app
        inner = _centered_card(self, pad_x=44, pad_y=32)

        theme.title(inner, "Gra z komputerem", size=24).pack(pady=(0, 20))
        self.color_var = tk.StringVar(value=game.WHITE)
        self.elo_var = tk.IntVar(value=game.DEFAULT_ELO)
        self.time_var = tk.DoubleVar(value=1.0)

        color_frame = tk.Frame(inner, bg=theme.SURFACE)
        color_frame.pack(pady=8, anchor="w", fill="x")
        theme.label(color_frame, "Twój kolor:").pack(side="left", padx=(0, 10))
        for text, value in (("Białe", game.WHITE), ("Czarne", game.BLACK)):
            tk.Radiobutton(color_frame, text=text, variable=self.color_var,
                           value=value, font=theme.ui_font(12),
                           bg=theme.SURFACE, fg=theme.TEXT,
                           activebackground=theme.SURFACE, activeforeground=theme.TEXT,
                           selectcolor=theme.SURFACE_LIGHT).pack(side="left")

        elo_frame = tk.Frame(inner, bg=theme.SURFACE)
        elo_frame.pack(pady=8, anchor="w", fill="x")
        theme.label(elo_frame, "Siła (ELO):").pack(side="left", padx=(0, 10))
        self._scale(elo_frame, 1320, 2850, 1, self.elo_var).pack(side="left")

        time_frame = tk.Frame(inner, bg=theme.SURFACE)
        time_frame.pack(pady=8, anchor="w", fill="x")
        theme.label(time_frame, "Czas na ruch (s):").pack(side="left", padx=(0, 10))
        self._scale(time_frame, 0.1, 5.0, 0.1, self.time_var).pack(side="left")

        theme.Button(inner, "Rozpocznij", command=self._start).pack(
            fill="x", pady=(20, 0))
        theme.Button(inner, "Powrót", kind="ghost",
                     command=self.app.show_menu).pack(fill="x", pady=(10, 0))

    @staticmethod
    def _scale(parent, frm, to, resolution, variable):
        return tk.Scale(parent, from_=frm, to=to, resolution=resolution,
                        orient="horizontal", length=240, variable=variable,
                        bg=theme.SURFACE, fg=theme.TEXT, troughcolor=theme.SURFACE_LIGHT,
                        highlightthickness=0, activebackground=theme.ACCENT,
                        font=theme.ui_font(10))

    def _start(self) -> None:
        try:
            provider = game.ComputerMoveProvider(self.elo_var.get(), self.time_var.get())
        except game.EngineNotFoundError as error:
            messagebox.showerror("Brak silnika", str(error))
            return
        self.app.show_computer_game(self.color_var.get(), provider)


class NetworkSetupScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=theme.BG)
        self.app = app
        inner = _centered_card(self, pad_x=40, pad_y=28)

        theme.title(inner, "Gra w sieci LAN", size=24).pack(pady=(0, 18))

        host_box = tk.Frame(inner, bg=theme.SURFACE_LIGHT,
                            highlightbackground=theme.BORDER, highlightthickness=1)
        host_box.pack(fill="x", pady=8)
        host_inner = tk.Frame(host_box, bg=theme.SURFACE_LIGHT)
        host_inner.pack(fill="x", padx=14, pady=12)
        theme.subtitle(host_inner, "Załóż grę (host)", size=12).pack(anchor="w")
        tk.Label(host_inner, text=f"Twój adres IP: {local_ip_address()}",
                 font=theme.mono_font(12), bg=theme.SURFACE_LIGHT,
                 fg=theme.TEXT).pack(anchor="w", pady=(6, 0))
        tk.Label(host_inner, text=f"Port: {protocol.DEFAULT_PORT}",
                 font=theme.mono_font(12), bg=theme.SURFACE_LIGHT,
                 fg=theme.TEXT).pack(anchor="w")
        theme.Button(host_inner, "Uruchom hosta i graj (Białe)",
                     command=self._host).pack(fill="x", pady=(10, 0))

        join_box = tk.Frame(inner, bg=theme.SURFACE_LIGHT,
                            highlightbackground=theme.BORDER, highlightthickness=1)
        join_box.pack(fill="x", pady=8)
        join_inner = tk.Frame(join_box, bg=theme.SURFACE_LIGHT)
        join_inner.pack(fill="x", padx=14, pady=12)
        theme.subtitle(join_inner, "Dołącz do gry (klient)", size=12).pack(anchor="w")
        row = tk.Frame(join_inner, bg=theme.SURFACE_LIGHT)
        row.pack(anchor="w", pady=(6, 0))
        tk.Label(row, text="Adres IP:", font=theme.ui_font(12),
                 bg=theme.SURFACE_LIGHT, fg=theme.TEXT).pack(side="left", padx=(0, 6))
        self.ip_var = tk.StringVar(value="127.0.0.1")
        theme.entry(row, textvariable=self.ip_var, width=16).pack(side="left", ipady=3)
        tk.Label(row, text="Port:", font=theme.ui_font(12),
                 bg=theme.SURFACE_LIGHT, fg=theme.TEXT).pack(side="left", padx=6)
        self.port_var = tk.IntVar(value=protocol.DEFAULT_PORT)
        theme.entry(row, textvariable=self.port_var, width=7).pack(side="left", ipady=3)
        theme.Button(join_inner, "Połącz i graj (Czarne)",
                     command=self._join).pack(fill="x", pady=(10, 0))

        theme.Button(inner, "Powrót", kind="ghost",
                     command=self.app.show_menu).pack(fill="x", pady=(14, 0))

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
        host = self.ip_var.get().strip()
        if not host:
            messagebox.showwarning("Połączenie", "Podaj adres IP hosta.")
            return
        try:
            port = int(self.port_var.get())
            if not (1 <= port <= 65535):
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showwarning("Połączenie", "Port musi być liczbą 1-65535.")
            return
        client = NetworkClient(host, port)
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
        self.configure(bg=theme.BG)
        self.resizable(False, False)
        self.selected_game = None

        theme.title(self, "Wybierz zapisaną grę", size=16).pack(pady=14)

        container = tk.Frame(self, bg=theme.BG)
        container.pack(padx=14, pady=4)

        for i, (game_id, date) in enumerate(games):
            card = tk.Frame(container, bg=theme.SURFACE,
                            highlightbackground=theme.BORDER, highlightthickness=1)
            card.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")
            inner = tk.Frame(card, bg=theme.SURFACE)
            inner.pack(padx=12, pady=12)

            theme.subtitle(inner, f"Gra #{game_id}", size=12).pack()
            theme.label(inner, str(date), size=10, muted=True).pack(pady=(2, 8))
            tk.Label(inner, text="♟", font=theme.piece_font(40),
                     bg=theme.SURFACE_LIGHT, fg=theme.ACCENT, width=4, height=2).pack()
            theme.Button(inner, "Wybierz", kind="ghost",
                         command=lambda gid=game_id: self._select(gid)).pack(
                fill="x", pady=(10, 0))

        theme.Button(self, "Anuluj", kind="ghost",
                     command=self.destroy).pack(pady=(6, 14))

    def _select(self, game_id):
        self.selected_game = game_id
        self.destroy()
