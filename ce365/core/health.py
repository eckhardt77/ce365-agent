"""
CE365 Agent - Health Check Module

Prüft System-Voraussetzungen und Konfiguration.
Wird verwendet von: ce365 --health und Post-Update Smoke Test.

Return-Code: 0 = OK, 1 = Fehler
"""

import sys
import importlib
from pathlib import Path
from rich.console import Console

console = Console()


def run_health_check() -> int:
    """
    Führt Health-Check durch und gibt Exit-Code zurück.

    Prüft:
    1. Python-Version (>= 3.9)
    2. Kritische Dependencies
    3. Config/API-Key vorhanden
    4. Anthropic API erreichbar
    5. Daten-Verzeichnisse

    Returns:
        0 = alles OK, 1 = Fehler gefunden
    """
    from ce365.__version__ import __version__

    console.print(f"\n[bold cyan]🩺 CE365 Health-Check v{__version__}[/bold cyan]\n")

    checks_passed = 0
    checks_failed = 0

    # 1. Python-Version
    py_version = sys.version_info
    if py_version >= (3, 9):
        _pass(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
        checks_passed += 1
    else:
        _fail(f"Python {py_version.major}.{py_version.minor} (benötigt >= 3.9)")
        checks_failed += 1

    # 2. Kritische Dependencies
    critical_deps = [
        ("anthropic", "Anthropic SDK"),
        ("rich", "Rich Console"),
        ("pydantic", "Pydantic"),
        ("httpx", "HTTPX"),
        ("psutil", "PSUtil"),
    ]

    for module_name, display_name in critical_deps:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "?")
            _pass(f"{display_name} ({version})")
            checks_passed += 1
        except ImportError:
            _fail(f"{display_name} nicht installiert")
            checks_failed += 1

    # 3. Config / API-Key
    try:
        from ce365.config.settings import get_settings
        settings = get_settings()
        if settings.anthropic_api_key and settings.anthropic_api_key != "test-key-not-real":
            _pass("API-Key konfiguriert")
            checks_passed += 1
        else:
            _fail("API-Key nicht konfiguriert")
            checks_failed += 1
    except Exception as e:
        _fail(f"Config-Fehler: {e}")
        checks_failed += 1

    # 4. Anthropic API Ping
    try:
        import httpx
        response = httpx.get(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": "ping", "anthropic-version": "2023-06-01"},
            timeout=5,
        )
        # 401 = API erreichbar (Key ungültig ist egal, Verbindung steht)
        if response.status_code in (401, 400):
            _pass("Anthropic API erreichbar")
            checks_passed += 1
        else:
            _warn(f"Anthropic API: HTTP {response.status_code}")
            checks_passed += 1
    except Exception as e:
        _fail(f"Anthropic API nicht erreichbar: {e}")
        checks_failed += 1

    # 5. Daten-Verzeichnisse
    data_dir = Path("data")
    ce365_dir = Path.home() / ".ce365"
    for dir_path, name in [(data_dir, "data/"), (ce365_dir, "~/.ce365/")]:
        if dir_path.exists():
            _pass(f"Verzeichnis {name} vorhanden")
            checks_passed += 1
        else:
            _warn(f"Verzeichnis {name} fehlt (wird beim Start erstellt)")
            checks_passed += 1

    # 6. Module importierbar
    try:
        from ce365.workflow.state_machine import WorkflowStateMachine
        from ce365.tools.registry import ToolRegistry
        from ce365.core.session import Session
        _pass("Kern-Module importierbar")
        checks_passed += 1
    except ImportError as e:
        _fail(f"Import-Fehler: {e}")
        checks_failed += 1

    # Summary
    console.print()
    if checks_failed == 0:
        console.print(f"[bold green]✅ Alle {checks_passed} Checks bestanden[/bold green]\n")
        return 0
    else:
        console.print(
            f"[bold red]❌ {checks_failed} Fehler, {checks_passed} OK[/bold red]\n"
        )
        return 1


def _pass(msg: str):
    console.print(f"  [green]✓[/green] {msg}")


def _fail(msg: str):
    console.print(f"  [red]✗[/red] {msg}")


def _warn(msg: str):
    console.print(f"  [yellow]⚠[/yellow] {msg}")
