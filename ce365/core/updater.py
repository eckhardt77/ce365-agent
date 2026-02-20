"""
CE365 Agent - Update & Rollback Module

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing

Zwei Modi:
- Community (pip): pip install --upgrade ce365-agent
- Pro (Binary): Download vom Lizenzserver, Binary ersetzen
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import platform as platform_mod
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console

import httpx

console = Console()

LICENSE_SERVER = "https://license.ce365.de"
CACHE_DIR = Path.home() / ".ce365"
CACHE_FILE = CACHE_DIR / "update_check.json"
BACKUP_DIR = CACHE_DIR / "backups"


# ============================================================
# PLATFORM DETECTION
# ============================================================

def _get_platform() -> str:
    """Aktuelle Plattform ermitteln"""
    system = platform_mod.system().lower()
    machine = platform_mod.machine().lower()

    if system == "darwin":
        arch = "arm64" if machine == "arm64" else "amd64"
        return f"macos-{arch}"
    elif system == "windows":
        arch = "amd64" if machine in ("amd64", "x86_64") else machine
        return f"win-{arch}"
    else:
        arch = "amd64" if machine in ("x86_64", "amd64") else machine
        return f"linux-{arch}"


def _is_binary() -> bool:
    """Prüfen ob wir als PyInstaller-Binary laufen"""
    return getattr(sys, "frozen", False)


# ============================================================
# UPDATE CHECK (Cache: 1x pro Tag)
# ============================================================

def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_cache(data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2))


def check_for_update(current_version: str) -> dict | None:
    """
    Prüft ob ein Update verfügbar ist. Max 1x pro Tag (Cache).

    Returns:
        dict mit update_available, latest_version, download_url
        oder None wenn kein Update / kein Check nötig
    """
    cache = _load_cache()
    last_check = cache.get("last_check")
    if last_check:
        try:
            last_dt = datetime.fromisoformat(last_check)
            if datetime.now() - last_dt < timedelta(hours=24):
                if cache.get("update_available"):
                    return cache
                return None
        except Exception:
            pass

    plat = _get_platform()
    try:
        resp = httpx.get(
            f"{LICENSE_SERVER}/api/update/check",
            params={"version": current_version, "platform": plat},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    data["last_check"] = datetime.now().isoformat()
    _save_cache(data)

    if data.get("update_available"):
        return data
    return None


# ============================================================
# PRO BINARY UPDATE
# ============================================================

def _download_binary(license_key: str, download_url: str) -> str | None:
    """Binary vom Lizenzserver herunterladen"""
    full_url = f"{LICENSE_SERVER}{download_url}?license_key={license_key}"

    try:
        with httpx.stream("GET", full_url, timeout=60.0) as resp:
            resp.raise_for_status()
            suffix = ".exe" if _get_platform().startswith("win") else ""
            fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="ce365-update-")
            with open(fd, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)

        if not _get_platform().startswith("win"):
            os.chmod(tmp_path, os.stat(tmp_path).st_mode | stat.S_IEXEC)

        return tmp_path
    except Exception as e:
        console.print(f"  [red]x[/red] Download-Fehler: {e}")
        return None


def _replace_binary(tmp_path: str) -> bool:
    """Aktuelle Binary durch neue ersetzen"""
    current_binary = sys.executable
    backup_path = current_binary + ".backup"

    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(current_binary, backup_path)
        shutil.move(tmp_path, current_binary)

        if not _get_platform().startswith("win"):
            os.chmod(current_binary, os.stat(current_binary).st_mode | stat.S_IEXEC)

        _save_cache({"last_check": datetime.now().isoformat(), "update_available": False})
        return True
    except Exception as e:
        console.print(f"  [red]x[/red] Update-Fehler: {e}")
        if os.path.exists(backup_path) and not os.path.exists(current_binary):
            os.rename(backup_path, current_binary)
        return False


# ============================================================
# COMMUNITY PIP UPDATE
# ============================================================

def _create_backup(version: str) -> Path | None:
    """Backup der aktuellen pip-Installation"""
    try:
        backup_path = BACKUP_DIR / f"v{version}"
        backup_path.mkdir(parents=True, exist_ok=True)
        import ce365
        package_dir = Path(ce365.__file__).parent
        if package_dir.exists():
            dest = backup_path / "ce365"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(package_dir, dest, dirs_exist_ok=True)
        (backup_path / "version.txt").write_text(version)
        return backup_path
    except Exception as e:
        console.print(f"  [yellow]![/yellow] Backup-Fehler: {e}")
        return None


def _restore_backup(version: str):
    """pip-Installation aus Backup wiederherstellen"""
    backup_path = BACKUP_DIR / f"v{version}"
    if not backup_path.exists():
        console.print(f"  [red]x[/red] Backup v{version} nicht gefunden")
        return
    try:
        backup_package = backup_path / "ce365"
        if not backup_package.exists():
            console.print(f"  [red]x[/red] Package-Backup nicht vorhanden")
            return
        import ce365
        target_dir = Path(ce365.__file__).parent
        shutil.copytree(backup_package, target_dir, dirs_exist_ok=True)
        console.print(f"  [green]v[/green] Version v{version} wiederhergestellt")
        console.print("  [dim]Neustart empfohlen[/dim]\n")
    except Exception as e:
        console.print(f"  [red]x[/red] Rollback-Fehler: {e}")


# ============================================================
# PUBLIC API
# ============================================================

def run_update(license_key: str = ""):
    """
    Kompletter Update-Prozess.
    - Binary: Check -> Download -> Replace
    - pip: Backup -> pip upgrade -> Health-Check
    """
    from ce365.__version__ import __version__

    console.print(f"\n[bold cyan]CE365 Update (v{__version__})[/bold cyan]\n")

    if _is_binary():
        # === Pro Binary Update ===
        console.print("  Modus: Binary (Pro)")

        # Lizenzschlüssel ermitteln
        if not license_key:
            try:
                from dotenv import dotenv_values
                env = dotenv_values()
                license_key = env.get("CE365_LICENSE_KEY", "")
            except Exception:
                pass

        if not license_key:
            console.print("  [red]x[/red] Lizenzschluessel benoetigt (CE365_LICENSE_KEY)")
            return

        # Update-Check (Force, kein Cache)
        plat = _get_platform()
        try:
            resp = httpx.get(
                f"{LICENSE_SERVER}/api/update/check",
                params={"version": __version__, "platform": plat},
                timeout=5.0,
            )
            update_info = resp.json()
        except Exception as e:
            console.print(f"  [red]x[/red] Server nicht erreichbar: {e}")
            return

        if not update_info.get("update_available"):
            console.print(f"  [green]v[/green] Bereits auf dem neuesten Stand (v{__version__})")
            return

        latest = update_info.get("latest_version", "?")
        console.print(f"  Neue Version: v{latest}")
        console.print(f"  Lade herunter...")

        tmp_path = _download_binary(license_key, update_info.get("download_url", ""))
        if not tmp_path:
            return

        console.print(f"  Installiere...")
        if _replace_binary(tmp_path):
            console.print(f"\n[green]Update auf v{latest} erfolgreich! Bitte neu starten.[/green]\n")
        else:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    else:
        # === Community pip Update ===
        console.print("  Modus: pip (Community)")

        backup_path = _create_backup(__version__)
        if backup_path:
            console.print(f"  [green]v[/green] Backup erstellt: {backup_path}")

        console.print("  Installiere Update...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "git+https://github.com/eckhardt77/ce365-agent.git"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                console.print(f"  [red]x[/red] pip install fehlgeschlagen:\n{result.stderr}")
                return
            console.print("  [green]v[/green] Package aktualisiert")
        except subprocess.TimeoutExpired:
            console.print("  [red]x[/red] Update-Timeout (120s)")
            return
        except Exception as e:
            console.print(f"  [red]x[/red] Update-Fehler: {e}")
            return

        # Health-Check
        console.print("  Health-Check...")
        try:
            from ce365.core.health import run_health_check
            exit_code = run_health_check()
            if exit_code != 0:
                console.print("\n[red]Health-Check fehlgeschlagen! Rollback...[/red]")
                _restore_backup(__version__)
                return
        except Exception:
            pass

        console.print("\n[green]Update erfolgreich![/green]\n")


def run_rollback():
    """Rollback zur vorherigen Version"""
    console.print("\n[bold cyan]CE365 Rollback[/bold cyan]\n")

    if _is_binary():
        # Binary Rollback
        current_binary = sys.executable
        backup_path = current_binary + ".backup"
        if not os.path.exists(backup_path):
            console.print("  [red]x[/red] Kein Backup gefunden")
            return
        try:
            os.remove(current_binary)
            os.rename(backup_path, current_binary)
            console.print("  [green]v[/green] Rollback erfolgreich. Bitte neu starten.")
        except Exception as e:
            console.print(f"  [red]x[/red] Rollback-Fehler: {e}")
    else:
        # pip Rollback
        if not BACKUP_DIR.exists():
            console.print("  [red]x[/red] Keine Backups vorhanden")
            return

        backups = sorted(BACKUP_DIR.iterdir(), reverse=True)
        if not backups:
            console.print("  [red]x[/red] Keine Backups vorhanden")
            return

        console.print("  Verfuegbare Backups:")
        for b in backups:
            console.print(f"    - {b.name}")

        latest = backups[0]
        console.print(f"\n  Stelle {latest.name} wieder her...")
        _restore_backup(latest.name.lstrip("v"))
