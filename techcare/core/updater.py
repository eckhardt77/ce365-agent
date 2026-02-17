"""
TechCare Bot - CLI Update & Rollback Module

Sichert aktuelle Version vor Update und ermöglicht Rollback.
Backup-Verzeichnis: ~/.techcare/backups/v{version}/
"""

import shutil
import subprocess
import sys
from pathlib import Path
from rich.console import Console

console = Console()

BACKUP_DIR = Path.home() / ".techcare" / "backups"


def run_update():
    """
    Aktualisiert TechCare CLI via pip.

    Flow:
    1. Aktuelle Version sichern
    2. pip install --upgrade techcare
    3. Health-Check
    4. Bei Fehler: Rollback
    """
    from techcare.__version__ import __version__
    from techcare.core.health import run_health_check

    console.print(f"\n[bold cyan]🔄 TechCare Update (aktuelle Version: v{__version__})[/bold cyan]\n")

    # 1. Backup erstellen
    backup_path = _create_backup(__version__)
    if backup_path:
        console.print(f"  [green]✓[/green] Backup erstellt: {backup_path}")
    else:
        console.print("  [yellow]⚠[/yellow] Backup konnte nicht erstellt werden")

    # 2. Update via pip
    console.print("\n  Installiere Update...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "techcare-bot"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            console.print(f"  [red]✗[/red] pip install fehlgeschlagen:\n{result.stderr}")
            return
        console.print("  [green]✓[/green] Package aktualisiert")
    except subprocess.TimeoutExpired:
        console.print("  [red]✗[/red] Update-Timeout (120s)")
        return
    except Exception as e:
        console.print(f"  [red]✗[/red] Update-Fehler: {e}")
        return

    # 3. Post-Update Health-Check
    console.print("\n  Führe Health-Check durch...")
    exit_code = run_health_check()

    if exit_code != 0:
        console.print("\n[red]❌ Health-Check fehlgeschlagen! Rollback wird durchgeführt...[/red]")
        _restore_backup(__version__)
    else:
        console.print("\n[green]✅ Update erfolgreich![/green]\n")


def run_rollback():
    """
    Rollback zur letzten gesicherten Version.

    Listet verfügbare Backups und stellt die letzte Version wieder her.
    """
    console.print("\n[bold cyan]⏪ TechCare Rollback[/bold cyan]\n")

    if not BACKUP_DIR.exists():
        console.print("  [red]✗[/red] Keine Backups vorhanden")
        return

    # Verfügbare Backups auflisten
    backups = sorted(BACKUP_DIR.iterdir(), reverse=True)
    if not backups:
        console.print("  [red]✗[/red] Keine Backups vorhanden")
        return

    console.print("  Verfügbare Backups:")
    for backup in backups:
        console.print(f"    • {backup.name}")

    latest = backups[0]
    version = latest.name

    console.print(f"\n  Stelle Version {version} wieder her...")
    _restore_backup(version.lstrip("v"))


def _create_backup(version: str) -> Path:
    """Erstellt Backup der aktuellen Installation"""
    try:
        backup_path = BACKUP_DIR / f"v{version}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Package-Pfad ermitteln
        import techcare
        package_dir = Path(techcare.__file__).parent

        # Package-Dateien kopieren
        if package_dir.exists():
            dest = backup_path / "techcare"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(package_dir, dest, dirs_exist_ok=True)

        # Version merken
        (backup_path / "version.txt").write_text(version)

        return backup_path

    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Backup-Fehler: {e}")
        return None


def _restore_backup(version: str):
    """Stellt Backup-Version wieder her"""
    backup_path = BACKUP_DIR / f"v{version}"

    if not backup_path.exists():
        console.print(f"  [red]✗[/red] Backup v{version} nicht gefunden")
        return

    try:
        backup_package = backup_path / "techcare"
        if not backup_package.exists():
            console.print(f"  [red]✗[/red] Package-Backup nicht vorhanden")
            return

        import techcare
        target_dir = Path(techcare.__file__).parent

        shutil.copytree(backup_package, target_dir, dirs_exist_ok=True)
        console.print(f"  [green]✓[/green] Version v{version} wiederhergestellt")
        console.print("  [dim]Neustart empfohlen[/dim]\n")

    except Exception as e:
        console.print(f"  [red]✗[/red] Rollback-Fehler: {e}")
