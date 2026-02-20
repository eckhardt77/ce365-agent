#!/usr/bin/env python3
"""
CE365 Agent — Binary Smoke Test
Prueft ob alle kritischen Module in der PyInstaller-Binary verfuegbar sind.

Usage:
    ./dist/ce365 scripts/smoke_test_binary.py     (innerhalb der Binary)
    python scripts/smoke_test_binary.py            (direkt, zum Testen)

Wird im CI nach dem Build ausgefuehrt:
    ./dist/ce365 --smoke-test   (oder direkt als Python-Skript)
"""

import sys

# Alle Module die in der Binary verfuegbar sein MUESSEN
REQUIRED_MODULES = [
    # Core
    'anthropic',
    'openai',
    'httpx',
    'rich',
    'pydantic',
    'psutil',
    'keyring',
    'bcrypt',
    'cryptography',
    # Database
    'aiosqlite',
    'sqlalchemy',
    'pymysql',
    # Tools
    'duckduckgo_search',
    'bs4',
    'lxml',
    'fpdf',
    # Pro-Features
    'asyncssh',
    'pypsrp',
    # PII (optional — spacy-Modell kann fehlen)
    'presidio_analyzer',
    'presidio_anonymizer',
]

# Module die optional sind (Warnung statt Fehler)
OPTIONAL_MODULES = [
    'asyncmy',
    'spacy',
    'de_core_news_sm',
]


def main():
    failed = []
    warned = []

    print("CE365 Binary Smoke Test")
    print("=" * 50)

    for mod in REQUIRED_MODULES:
        try:
            __import__(mod)
            print(f"  OK  {mod}")
        except ImportError as e:
            print(f"  FAIL  {mod} — {e}")
            failed.append(mod)

    print()
    for mod in OPTIONAL_MODULES:
        try:
            __import__(mod)
            print(f"  OK  {mod} (optional)")
        except ImportError:
            print(f"  WARN  {mod} (optional, nicht verfuegbar)")
            warned.append(mod)

    print()
    print("=" * 50)
    print(f"Required: {len(REQUIRED_MODULES) - len(failed)}/{len(REQUIRED_MODULES)} OK")
    if warned:
        print(f"Optional: {len(warned)} nicht verfuegbar")
    if failed:
        print(f"\nFEHLER: {len(failed)} Module fehlen: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nAlle kritischen Module verfuegbar.")
        sys.exit(0)


if __name__ == '__main__':
    main()
