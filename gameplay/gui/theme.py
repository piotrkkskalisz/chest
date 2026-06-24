from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from collections.abc import Callable


BG = "#2e2722"
SURFACE = "#3d342c"
SURFACE_LIGHT = "#4a3f35"
BORDER = "#5c4d3f"

ACCENT = "#c19a6b"
ACCENT_HOVER = "#d4ad7c"
ACCENT_DARK = "#a87f53"
DANGER = "#b5544a"
DANGER_HOVER = "#000000"

TEXT = "#f2e8dc"
TEXT_MUTED = "#c2b2a0"
TEXT_ON_ACCENT = "#2e2722"


BOARD_LIGHT = "#f0d9b5"
BOARD_DARK = "#b58863"
SQ_SELECTED = "#f6eb74"
SQ_TARGET = "#7fae5f"
SQ_LAST = "#cdd26a"
SQ_CHECK = "#e06c6c"
PIECE_DARK = "#2b2620"
PIECE_LIGHT = "#fbf4e8"
PIECE_OUTLINE = "#1c1814"


_TITLE_FAMILIES = ("Georgia", "Cambria", "Times New Roman", "serif")
_UI_FAMILIES = ("Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial")
_MONO_FAMILIES = ("Consolas", "DejaVu Sans Mono", "Courier New", "monospace")
_PIECE_FAMILIES = ("Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS", "FreeSerif")


def _first_available(candidates: tuple[str, ...], default: str) -> str:
    try:
        installed = set(tkfont.families())
    except tk.TclError:
        return default
    for name in candidates:
        if name in installed:
            return name
    return default


TITLE_FAMILY = _UI_FAMILIES[0]
UI_FAMILY = _UI_FAMILIES[0]
MONO_FAMILY = _MONO_FAMILIES[0]
PIECE_FAMILY = _PIECE_FAMILIES[0]


def init(root: tk.Tk) -> None:
    global TITLE_FAMILY, UI_FAMILY, MONO_FAMILY, PIECE_FAMILY
    TITLE_FAMILY = _first_available(_TITLE_FAMILIES, _UI_FAMILIES[0])
    UI_FAMILY = _first_available(_UI_FAMILIES, "TkDefaultFont")
    MONO_FAMILY = _first_available(_MONO_FAMILIES, "TkFixedFont")
    PIECE_FAMILY = _first_available(_PIECE_FAMILIES, "TkDefaultFont")
    root.configure(bg=BG)


def title_font(size: int = 26) -> tuple:
    return (TITLE_FAMILY, size, "bold")


def ui_font(size: int = 12, bold: bool = False) -> tuple:
    return (UI_FAMILY, size, "bold") if bold else (UI_FAMILY, size)


def mono_font(size: int = 11) -> tuple:
    return (MONO_FAMILY, size)


def piece_font(size: int) -> tuple:
    return (PIECE_FAMILY, size)


def screen(master: tk.Misc) -> tk.Frame:
    return tk.Frame(master, bg=BG)


def card(master: tk.Misc, **kwargs) -> tk.Frame:
    return tk.Frame(master, bg=SURFACE, highlightbackground=BORDER,
                    highlightthickness=1, **kwargs)


def title(master: tk.Misc, text: str, size: int = 26) -> tk.Label:
    return tk.Label(master, text=text, font=title_font(size), bg=master["bg"],
                    fg=TEXT)


def subtitle(master: tk.Misc, text: str, size: int = 15) -> tk.Label:
    return tk.Label(master, text=text, font=ui_font(size, bold=True),
                    bg=master["bg"], fg=ACCENT)


def label(master: tk.Misc, text: str, size: int = 12, muted: bool = False,
          **kwargs) -> tk.Label:
    return tk.Label(master, text=text, font=ui_font(size),
                    bg=kwargs.pop("bg", master["bg"]),
                    fg=TEXT_MUTED if muted else TEXT, **kwargs)


def entry(master: tk.Misc, **kwargs) -> tk.Entry:
    return tk.Entry(master, font=ui_font(12), bg=SURFACE_LIGHT, fg=TEXT,
                    insertbackground=TEXT, relief="flat",
                    highlightbackground=BORDER, highlightcolor=ACCENT,
                    highlightthickness=1, **kwargs)


class Button(tk.Button):

    _PALETTES: dict[str, tuple[str, str, str, str]] = {
        "primary": (ACCENT, ACCENT_HOVER, ACCENT_DARK, TEXT_ON_ACCENT),
        "ghost": (SURFACE_LIGHT, BORDER, ACCENT_DARK, TEXT),
        "danger": (DANGER, DANGER_HOVER, ACCENT_DARK, TEXT),
    }

    def __init__(self, master: tk.Misc, text: str, command: Callable[[], None] = lambda: None,
                 kind: str = "primary", **kwargs):
        base, hover, active, fg = self._PALETTES.get(kind, self._PALETTES["primary"])
        self._base = base
        self._hover = hover
        super().__init__(
            master, text=text, command=command,
            font=ui_font(12, bold=(kind == "primary")),
            bg=base, fg=fg, activebackground=active, activeforeground=fg,
            relief="flat", borderwidth=0, cursor="hand2",
            padx=kwargs.pop("padx", 16), pady=kwargs.pop("pady", 8),
            highlightthickness=0, **kwargs,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event) -> None:
        if str(self["state"]) != "disabled":
            self.configure(bg=self._hover)

    def _on_leave(self, _event) -> None:
        self.configure(bg=self._base)
