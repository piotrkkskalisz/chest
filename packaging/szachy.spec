from PyInstaller.building.datastruct import Tree

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['.'],
    binaries=[],
    datas=[("../gameplay/game_logic/stockfish/stockfish-windows-x86-64-avx2.exe", "gameplay/game_logic/stockfish")],
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
