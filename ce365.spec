# -*- mode: python ; coding: utf-8 -*-
"""
CE365 Agent — PyInstaller Spec
Erstellt portable Binaries (Windows .exe / macOS Binary)

Usage:
    pyinstaller ce365.spec

Output:
    dist/ce365       (macOS)
    dist/ce365.exe   (Windows)
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Projekt-Root
PROJECT_ROOT = os.path.abspath('.')

# spaCy-Modell finden (falls installiert)
spacy_data = []
try:
    import de_core_news_sm
    model_path = Path(de_core_news_sm.__path__[0])
    spacy_data = [(str(model_path), 'de_core_news_sm')]
except ImportError:
    print("WARNUNG: de_core_news_sm nicht gefunden — wird nicht eingebettet")

# Hidden Imports — alle Dependencies die PyInstaller nicht automatisch findet
hidden_imports = [
    'anthropic',
    'openai',
    'httpx',
    'httpx._transports',
    'httpx._transports.default',
    'rich',
    'rich.console',
    'rich.panel',
    'rich.prompt',
    'rich.table',
    'rich.text',
    'rich.progress',
    'rich.markdown',
    'pydantic',
    'pydantic.deprecated',
    'pydantic.deprecated.decorator',
    'dotenv',
    'psutil',
    'passlib',
    'passlib.hash',
    'passlib.handlers',
    'passlib.handlers.bcrypt',
    'bcrypt',
    'keyring',
    'keyring.backends',
    'aiosqlite',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'cryptography',
    'duckduckgo_search',
    'bs4',
    'lxml',
    'ce365',
    'ce365.core',
    'ce365.core.bot',
    'ce365.core.license',
    'ce365.core.health',
    'ce365.core.updater',
    'ce365.config',
    'ce365.config.settings',
    'ce365.setup',
    'ce365.setup.wizard',
    'ce365.setup.embedded_config',
    'ce365.setup.package_generator',
    'ce365.__version__',
    'ce365.__main__',
]

# Daten-Dateien
datas = [
    # Embedded Config Template (wird beim Build durch echte Config ersetzt)
]
datas += spacy_data

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'ce365', '__main__.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ce365',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
