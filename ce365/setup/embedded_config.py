"""
CE365 Agent — Embedded Config Module

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Dieses Modul wird beim Generieren eines Kunden-Pakets
mit den Techniker-Daten befüllt. Im Quellcode bleibt
EMBEDDED = False (kein Kunden-Paket).

Der PackageGenerator ersetzt EMBEDDED und CONFIG vor dem
PyInstaller-Build und stellt sie danach wieder zurück.
"""

# Wird vom PackageGenerator auf True gesetzt
EMBEDDED = False

# Wird vom PackageGenerator mit Techniker-Config befüllt
CONFIG = {}


def is_embedded() -> bool:
    """Prüft ob diese Binary ein eingebettetes Kunden-Paket ist"""
    return EMBEDDED and bool(CONFIG)


def get_config() -> dict:
    """Gibt die eingebettete Konfiguration zurück"""
    if not is_embedded():
        return {}
    return CONFIG.copy()
