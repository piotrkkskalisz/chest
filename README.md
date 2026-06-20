# Szachy (Python + python-chess + tkinter)

Aplikacja szachowa w Pythonie z graficznym interfejsem opartym na `tkinter`.
Tryby gry: dwie osoby lokalnie (hot-seat), gra z komputerem (Stockfish) oraz
gra dwóch osób w sieci lokalnej (LAN) w architekturze host–klient.

Figury rysowane są symbolami Unicode, więc aplikacja nie wymaga żadnych grafik.

## Funkcje

- Pełne reguły szachowe (legalne ruchy, szach, mat, pat, remis, roszada,
  en passant, promocja pionka) dzięki bibliotece `python-chess`.
- Menu główne z wyborem trybu gry.
- Gra lokalna dwóch osób na jednym komputerze.
- Gra z komputerem (Stockfish) z regulacją siły (ELO) i czasu na ruch.
- Gra w sieci LAN (TCP + JSON) – host zakłada serwer, klient dołącza po adresie IP.
- Historia ruchów w notacji SAN.
- Zapis i odczyt partii w formacie PGN (tryb lokalny).
- Podświetlanie wybranego pola, możliwych ruchów, ostatniego ruchu i szacha.

## Struktura projektu

```
chessPython/
├── main.py                       # punkt wejścia – uruchamia GUI
├── requirements.txt
├── README.md
├── docs/
├── assets/                       # zasoby (puste – figury są tekstowe)
├── saves/                        # zapisane partie PGN
├── tests/                        # testy pytest
└── gameplay/
    ├── game_logic/
    │   ├── game.py               # logika gry (klasa Game)
    │   └── stockfish/            # tutaj umieść silnik Stockfish
    ├── gui/
    │   ├── app.py                # kontroler okna i przełączanie ekranów
    │   ├── board_view.py         # widżet szachownicy
    │   └── screens.py            # menu i ekrany trybów gry
    └── network/
        ├── protocol.py           # komunikaty JSON
        ├── server.py             # serwer (host) – stan i walidacja
        └── client.py             # klient sieciowy
```

## Wymagania

- Python 3.12 lub nowszy (kod korzysta ze składni `type ...` i `@override`)
- biblioteka `python-chess`
- `tkinter` (zwykle dostępny w instalacji Pythona; na Linuksie: `sudo apt install python3-tk`)
- Stockfish – tylko dla trybu gry z komputerem

## Instalacja

```bash
git clone <adres-repozytorium>
cd chessPython
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Stockfish (gra z komputerem)

Pobierz Stockfisha ze strony https://stockfishchess.org/download/ i umieść plik
wykonywalny w katalogu `gameplay/game_logic/stockfish/`. Aplikacja automatycznie
wykryje dowolny plik, którego nazwa zaczyna się od `stockfish`. Bez silnika
pozostałe tryby działają normalnie.

## Uruchomienie

```bash
python main.py
```

## Gra w sieci LAN

1. Host wybiera „Gra w sieci LAN” → „Uruchom hosta i graj (Białe)” i podaje
   drugiej osobie swój adres IP wyświetlony na ekranie.
2. Klient wybiera „Gra w sieci LAN”, wpisuje adres IP hosta i klika
   „Połącz i graj (Czarne)”.
3. Obie osoby muszą znajdować się w tej samej sieci lokalnej. Na hoście może być
   konieczne zezwolenie Pythonowi na połączenia przychodzące w zaporze sieciowej.

Pełny opis działania znajduje się w `docs/documentation.html`.
