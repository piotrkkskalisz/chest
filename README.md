# Szachy (Python + python-chess + tkinter)

Aplikacja szachowa w Pythonie z graficznym interfejsem opartym na `tkinter`.
Tryby gry: dwie osoby lokalnie (hot-seat), gra z komputerem (Stockfish) oraz
gra dwoch osob w sieci lokalnej (LAN) w architekturze host-klient.

Figury rysowane sa symbolami Unicode na plotnie (`tkinter.Canvas`), wiec
aplikacja nie wymaga zadnych grafik, a plansza skaluje sie do rozmiaru okna.

## Funkcje

- Pelne reguly szachowe (legalne ruchy, szach, mat, pat, remis, roszada,
  en passant, promocja pionka) dzieki bibliotece `python-chess`.
- Logowanie i rejestracja uzytkownikow (konta w bazie SQLite).
- Gra lokalna dwoch osob na jednym komputerze.
- Gra z komputerem (Stockfish) z regulacja sily (ELO) i czasu na ruch.
- Gra w sieci LAN (TCP + JSON) - host zaklada serwer, klient dolacza po IP.
- Historia ruchow w notacji SAN, podswietlanie pol, ostatniego ruchu i szacha.
- Zapis i odczyt partii: w bazie danych (na konto gracza) oraz w plikach PGN.
- Nowoczesny, "drewniany" motyw graficzny; okno automatycznie dopasowuje sie
  do rozdzielczosci ekranu i jest wysrodkowane.

## Struktura projektu

```
chest/
├── main.py                       # punkt wejscia - inicjuje baze i uruchamia GUI
├── requirements.txt              # zaleznosci uruchomieniowe
├── requirements-dev.txt          # zaleznosci deweloperskie (testy, pakowanie)
├── build.bat / build.sh          # skrypty budujace pakiet (PyInstaller)
├── README.md
├── packaging/
│   └── szachy.spec               # konfiguracja PyInstaller
├── docs/
│   └── documentation.html        # pelna dokumentacja techniczna
├── assets/                       # zasoby (puste - figury sa tekstowe)
├── saves/                        # zapisane partie PGN
├── database/
│   ├── database.py               # warstwa dostepu do SQLite (uzytkownicy, gry)
│   └── database.sqlite           # plik bazy danych (tworzony automatycznie)
├── tests/                        # testy pytest (logika, baza, siec, walidacja)
└── gameplay/
    ├── auth.py                   # logowanie / rejestracja
    ├── game_logic/
    │   ├── game.py               # logika gry (klasa Game) + silnik Stockfish
    │   └── stockfish/            # tutaj umiesc silnik Stockfish
    ├── gui/
    │   ├── app.py                # kontroler okna i przelaczanie ekranow
    │   ├── theme.py              # centralny motyw (kolory, czcionki, widgety)
    │   ├── board_view.py         # widget szachownicy (Canvas)
    │   └── screens.py            # menu i ekrany trybow gry
    └── network/
        ├── protocol.py           # komunikaty JSON
        ├── server.py             # serwer (host) - stan i walidacja
        └── client.py             # klient sieciowy
```

## Wymagania

- Python 3.10 lub nowszy
- biblioteka `python-chess`
- `tkinter` (zwykle dostepny w instalacji Pythona; na Linuksie:
  `sudo apt install python3-tk`)
- Stockfish - tylko dla trybu gry z komputerem

## Instalacja

```bash
git clone <adres-repozytorium>
cd chest
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Stockfish (gra z komputerem)

Pobierz Stockfisha ze strony https://stockfishchess.org/download/ i umiesc plik
wykonywalny w katalogu `gameplay/game_logic/stockfish/`. Aplikacja automatycznie
wykryje dowolny plik, ktorego nazwa zaczyna sie od `stockfish`. Bez silnika
pozostale tryby dzialaja normalnie.

## Uruchomienie

```bash
python main.py
```

## Testy

```bash
pip install -r requirements-dev.txt
pytest
```

Testy obejmuja logike gry, warstwe bazy danych, uwierzytelnianie, walidacje
danych wejsciowych oraz komunikacje sieciowa - niezaleznie od interfejsu.

## Budowanie pakietu (PyInstaller)

```bash
# Windows
build.bat
# Linux / macOS
./build.sh
```

Gotowa aplikacja pojawi sie w katalogu `dist/Szachy/`.

## Gra w sieci LAN

1. Host wybiera "Gra w sieci LAN" -> "Uruchom hosta i graj (Biale)" i podaje
   drugiej osobie swoj adres IP wyswietlony na ekranie.
2. Klient wybiera "Gra w sieci LAN", wpisuje adres IP hosta i klika
   "Polacz i graj (Czarne)".
3. Obie osoby musza znajdowac sie w tej samej sieci lokalnej. Na hoscie moze byc
   konieczne zezwolenie Pythonowi na polaczenia przychodzace w zaporze sieciowej.

Pelny opis dzialania znajduje sie w `docs/documentation.html`, a szczegolowe
objasnienie skladni i logiki kazdego pliku - w `docs/objasnienie_kodu.html`.
