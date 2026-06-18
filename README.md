# chest

Chest aplication for playing online and offline.

Gra w szachy w Pythonie z graficznym interfejsem opartym na `tkinter`.
Tryb gry: dwóch graczy lokalnie (hot-seat). Figury rysowane są symbolami Unicode.

## Struktura projektu

```
chest/
├── main.py                       # punkt wejścia – uruchamia GUI
├── requirements.txt              # zależności (python-chess)
├── README.md
└── gameplay/
    ├── game-logic/
    │   └── game.py               # logika gry (klasa Game, oparta na python-chess)
    └── gui/
        └── gui.py                # interfejs graficzny (tkinter)
```

## Wymagania

- Python 3.12 lub nowszy (kod gry korzysta ze składni `type ...`)
- biblioteka `python-chess`
- `tkinter` (w większości instalacji Pythona dostępny domyślnie; na Linuxie może wymagać pakietu `python3-tk`)

## Instalacja

```bash
git clone <adres-repozytorium>
cd chest
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uruchomienie

```bash
python main.py
```

## Jak grać

Kliknij figurę gracza, którego jest ruch – podświetlą się dozwolone pola.
Następnie kliknij pole docelowe, aby wykonać ruch.
Pasek u góry pokazuje, czyj jest ruch oraz stan gry (szach, szach-mat, pat).
Przycisk „Nowa gra” resetuje planszę.
