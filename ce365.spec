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
from PyInstaller.utils.hooks import collect_submodules

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
    'sqlalchemy.dialects.mysql',
    'asyncmy',
    'pymysql',
    'asyncssh',
    'pypsrp',
    'presidio_analyzer',
    'presidio_anonymizer',
] + collect_submodules('asyncssh') + collect_submodules('pypsrp') + collect_submodules('presidio_analyzer') + collect_submodules('presidio_anonymizer') + [
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
    'fpdf',
]

# rich._unicode_data Module (dynamisch geladen, Bindestriche im Namen)
import rich._unicode_data
rich_unicode_dir = os.path.dirname(rich._unicode_data.__file__)
rich_unicode_data = [(rich_unicode_dir, 'rich/_unicode_data')]

# i18n Sprachdateien
i18n_dir = os.path.join(PROJECT_ROOT, 'ce365', 'i18n', 'languages')
i18n_data = [(i18n_dir, 'ce365/i18n/languages')]

# Font-Assets (DejaVu Sans fuer Unicode-PDF-Reports)
font_dir = os.path.join(PROJECT_ROOT, 'ce365', 'assets')
font_data = [(font_dir, 'ce365/assets')]

# asyncmy komplett einbinden (Cython-Extensions + Submodule), falls installiert
asyncmy_data = []
try:
    import asyncmy
    asyncmy_dir = os.path.dirname(asyncmy.__file__)
    asyncmy_data = [
        (asyncmy_dir, 'asyncmy'),
        (os.path.join(asyncmy_dir, 'constants'), 'asyncmy/constants'),
    ]
    # Replication-Submodul falls vorhanden
    if os.path.isdir(os.path.join(asyncmy_dir, 'replication')):
        asyncmy_data.append((os.path.join(asyncmy_dir, 'replication'), 'asyncmy/replication'))
except ImportError:
    print("WARNUNG: asyncmy nicht gefunden — wird nicht eingebettet")

# Daten-Dateien
datas = [
    # Embedded Config Template (wird beim Build durch echte Config ersetzt)
]
datas += i18n_data
datas += spacy_data
datas += rich_unicode_data
datas += asyncmy_data
datas += font_data

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
        'pandas',
        'scipy',
        'PIL',
        'pytest',
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
