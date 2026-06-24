from PyInstaller.building.datastruct import Tree
from pathlib import Path
from glob import glob
block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['.'],
    binaries=[],
    datas = [
        (str(Path(file).resolve()), "gameplay/game_logic/stockfish")
        for file in glob("gameplay/game_logic/stockfish/*")
    ],
    hiddenimports=['chess', 'chess.engine', 'chess.pgn'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Szachy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Szachy',
)
