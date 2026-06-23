@echo off
REM Buduje samodzielna aplikacje Szachy (Windows) przy uzyciu PyInstaller.
setlocal
python -m pip install --upgrade pyinstaller >nul 2>&1
python -m PyInstaller --noconfirm packaging\szachy.spec
echo.
echo Gotowe. Uruchom: dist\Szachy\Szachy.exe
endlocal
