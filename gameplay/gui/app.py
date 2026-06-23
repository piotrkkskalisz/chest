import tkinter as tk

from . import screens
from . import theme


SCREEN_FRACTION = 0.82
MIN_WIDTH = 900
MIN_HEIGHT = 680


class ChessApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Szachy")
        theme.init(root)
        self._configure_window()

        self.container = tk.Frame(root, bg=theme.BG)
        self.container.pack(fill="both", expand=True)
        self._current: tk.Frame | None = None
        self.user_id = None
        self.show_login()

    def _configure_window(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = max(MIN_WIDTH, min(int(screen_w * SCREEN_FRACTION), screen_w - 80))
        height = max(MIN_HEIGHT, min(int(screen_h * SCREEN_FRACTION), screen_h - 120))
        width = min(width, screen_w)
        height = min(height, screen_h)
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 3)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.root.minsize(min(MIN_WIDTH, screen_w), min(MIN_HEIGHT, screen_h))

    def _switch(self, factory) -> None:
        if self._current is not None:
            cleanup = getattr(self._current, "cleanup", None)
            if callable(cleanup):
                cleanup()
            self._current.destroy()
        self._current = factory(self.container, self)
        self._current.pack(fill="both", expand=True)

    def set_user(self, user_id) -> None:
        self.user_id = user_id

    def show_login(self) -> None:
        self._switch(screens.LoginScreen)

    def show_register(self) -> None:
        self._switch(screens.RegisterScreen)

    def show_menu(self) -> None:
        self._switch(screens.MenuScreen)

    def show_local_game(self) -> None:
        self._switch(screens.LocalGameScreen)

    def show_computer_setup(self) -> None:
        self._switch(screens.ComputerSetupScreen)

    def show_computer_game(self, human_color, provider) -> None:
        self._switch(lambda master, app: screens.ComputerGameScreen(
            master, app, human_color, provider))

    def show_network_setup(self) -> None:
        self._switch(screens.NetworkSetupScreen)

    def show_network_game(self, client, server) -> None:
        self._switch(lambda master, app: screens.NetworkGameScreen(
            master, app, client, server))

    def quit_app(self) -> None:
        if self._current is not None:
            cleanup = getattr(self._current, "cleanup", None)
            if callable(cleanup):
                cleanup()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = ChessApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
