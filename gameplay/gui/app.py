import tkinter as tk

from . import screens


class ChessApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Szachy")
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)
        self._current: tk.Frame | None = None
        self.user_id = None
        self.show_login()

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
    root.resizable(False, False)
    app = ChessApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
