#!/usr/bin/env bash
# Buduje samodzielna aplikacje Szachy (Linux/macOS) przy uzyciu PyInstaller.
set -e
python3 -m pip install --upgrade pyinstaller
python3 -m PyInstaller --noconfirm packaging/szachy.spec
echo
echo "Gotowe. Uruchom: dist/Szachy/Szachy"
