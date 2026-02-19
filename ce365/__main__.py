"""
CE365 Agent - AI-powered IT Maintenance Assistant

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License
"""

import asyncio
import sys
import argparse
import shutil
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from passlib.context import CryptContext
from ce365.core.bot import CE365Bot
from ce365.setup.wizard import run_setup_if_needed
from ce365.config.settings import get_settings
from ce365.core.health import run_health_check


console = Console()


def _show_embedded_banner(config: dict):
    """Zeigt Techniker-Info beim Start eines Kunden-Pakets"""
    from ce365.__version__ import __version__
    from rich.panel import Panel
    from rich.text import Text

    tech_name = config.get("_TECHNICIAN_NAME", "Techniker")
    company = config.get("_COMPANY", "")
    edition = config.get("EDITION", "community").title()

    banner = Text()
    banner.append(f"CE365 Agent v{__version__} — {edition} Edition\n", style="bold cyan")
    banner.append(f"Techniker: {tech_name}\n", style="bold")
    if company:
        banner.append(f"Lizenziert für: {company}", style="bold")

    console.print()
    console.print(Panel(banner, border_style="cyan", padding=(1, 1)))
    console.print()


def verify_technician_password() -> bool:
    """
    Prüft Techniker-Passwort beim Start

    Returns:
        True wenn korrekt oder kein Passwort gesetzt
        False wenn Passwort falsch (3 Versuche)
    """
    try:
        settings = get_settings()

        # Kein Passwort gesetzt = direkter Zugang
        if not settings.technician_password_hash:
            return True

        console.print("\n[bold cyan]🔐 CE365 Zugriff[/bold cyan]")
        console.print("[dim]Techniker-Passwort erforderlich[/dim]\n")

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # 3 Versuche
        for attempt in range(3):
            password = Prompt.ask("Passwort", password=True)

            if pwd_context.verify(password, settings.technician_password_hash):
                console.print("[green]✓ Authentifiziert[/green]\n")
                return True

            remaining = 2 - attempt
            if remaining > 0:
                console.print(f"[red]❌ Falsches Passwort ({remaining} Versuche übrig)[/red]\n")
            else:
                console.print("[red]❌ Zugriff verweigert[/red]\n")

        return False

    except Exception as e:
        console.print(f"[red]Fehler bei Passwort-Prüfung: {str(e)}[/red]")
        return False


def uninstall():
    """Deinstalliert CE365 CLI"""
    console.print("\n[bold red]🗑️  CE365 Deinstallation[/bold red]\n")

    console.print("Folgende Daten werden gelöscht:")
    console.print("  • .env Datei (API-Key, Konfiguration)")
    console.print("  • data/ Verzeichnis (Sessions, Changelogs, Cases)")
    console.print("  • ~/.ce365/ (User-Config, Cache)")
    console.print()

    if not Confirm.ask("[red]Wirklich deinstallieren?[/red]", default=False):
        console.print("\n[yellow]Deinstallation abgebrochen.[/yellow]")
        return

    try:
        # .env löschen
        env_file = Path(".env")
        if env_file.exists():
            env_file.unlink()
            console.print("[green]✓ .env gelöscht[/green]")

        # data/ löschen
        data_dir = Path("data")
        if data_dir.exists():
            shutil.rmtree(data_dir)
            console.print("[green]✓ data/ gelöscht[/green]")

        # ~/.ce365/ löschen
        user_dir = Path.home() / ".ce365"
        if user_dir.exists():
            shutil.rmtree(user_dir)
            console.print("[green]✓ ~/.ce365/ gelöscht[/green]")

        console.print("\n[green]✅ CE365 erfolgreich deinstalliert![/green]")
        console.print("\n[dim]Hinweis: Das Python-Package bleibt installiert.[/dim]")
        console.print("[dim]Deinstalliere mit: pip uninstall ce365[/dim]\n")

    except Exception as e:
        console.print(f"\n[red]❌ Fehler bei Deinstallation: {str(e)}[/red]")
        sys.exit(1)


def set_password():
    """Setzt oder ändert das Techniker-Passwort"""
    console.print("\n[bold cyan]🔐 Techniker-Passwort setzen[/bold cyan]\n")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    while True:
        password = Prompt.ask("Neues Passwort", password=True)

        if not password:
            console.print("\n[yellow]Abgebrochen.[/yellow]")
            return

        if len(password) < 6:
            console.print("\n[red]❌ Passwort zu kurz (min. 6 Zeichen)[/red]\n")
            continue

        confirm = Prompt.ask("Passwort wiederholen", password=True)

        if password != confirm:
            console.print("\n[red]❌ Passwörter stimmen nicht überein[/red]\n")
            continue

        # Hash erstellen
        password_hash = pwd_context.hash(password)

        # In .env schreiben
        env_file = Path(".env")
        if not env_file.exists():
            console.print("\n[red]❌ .env Datei nicht gefunden. Führe Setup aus.[/red]")
            return

        content = env_file.read_text()

        # TECHNICIAN_PASSWORD_HASH ersetzen oder hinzufügen
        if "TECHNICIAN_PASSWORD_HASH=" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("TECHNICIAN_PASSWORD_HASH="):
                    lines[i] = f"TECHNICIAN_PASSWORD_HASH={password_hash}"
                    break
            content = "\n".join(lines)
        else:
            content += f"\nTECHNICIAN_PASSWORD_HASH={password_hash}\n"

        env_file.write_text(content)

        console.print("\n[green]✓ Passwort erfolgreich gesetzt![/green]\n")
        return


async def _run_with_license_session(bot):
    """
    Führt den Bot mit Lizenz-Session-Management aus

    - Startet Session beim Lizenzserver (Pro)
    - Heartbeats alle 5 Minuten
    - Session-Release beim Beenden
    """
    session_manager = None

    try:
        # Session starten (nur Pro mit Lizenz + Server-URL)
        settings = get_settings()
        if settings.edition == "pro" and settings.license_key and settings.license_server_url:
            from ce365.core.license import SessionManager
            session_manager = SessionManager(
                settings.license_server_url, settings.license_key
            )
            result = await session_manager.start_session()

            if result.get("success"):
                session_manager.start_heartbeat_timer()
            else:
                error = result.get("error", "")
                if "Seat" in error or "belegt" in error:
                    console.print(f"\n[red]❌ {error}[/red]")
                    console.print("[dim]Bitte beende die andere Session zuerst.[/dim]\n")
                    return
                # Server offline → trotzdem starten
                console.print(f"[yellow]⚠ Lizenz-Session: {error}[/yellow]")
                session_manager = None

        # Bot starten
        await bot.run()

    finally:
        # Session immer freigeben
        if session_manager:
            session_manager.stop_heartbeat_timer()
            await session_manager.release_session()


def main():
    """Main Entry Point für CE365 Agent"""
    # CLI-Argumente parsen
    parser = argparse.ArgumentParser(
        description="CE365 Agent - AI-powered IT Maintenance Assistant"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Deinstalliert CE365 (löscht Daten und Config)"
    )
    parser.add_argument(
        "--set-password",
        action="store_true",
        help="Setzt oder ändert das Techniker-Passwort"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Zeigt Version an"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Führt Health-Check durch (Python, Dependencies, API, Config)"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Aktualisiert CE365 auf die neueste Version"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback zur letzten Backup-Version"
    )
    parser.add_argument(
        "--generate-package",
        action="store_true",
        help="Generiert ein portables Kunden-Paket (.exe/.app)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup-Wizard erneut ausführen"
    )

    args = parser.parse_args()

    # Befehle ausführen
    if args.uninstall:
        uninstall()
        return

    if args.set_password:
        set_password()
        return

    if args.version:
        from ce365.__version__ import __version__, __edition__
        mode = "Binary" if getattr(sys, "frozen", False) else "pip"
        print(f"CE365 Agent v{__version__} ({__edition__} Edition, {mode})")
        return

    if args.health:
        exit_code = run_health_check()
        sys.exit(exit_code)

    if args.update:
        from ce365.core.updater import run_update
        run_update()
        return

    if args.rollback:
        from ce365.core.updater import run_rollback
        run_rollback()
        return

    if args.generate_package:
        from ce365.setup.package_generator import run_generate_package
        success = run_generate_package()
        sys.exit(0 if success else 1)

    if args.setup:
        from ce365.setup.wizard import SetupWizard
        wizard = SetupWizard()
        if wizard.run():
            console.print("[green]Setup abgeschlossen![/green]")
        else:
            console.print("[yellow]Setup abgebrochen.[/yellow]")
        return

    # Normaler Start
    try:
        # Embedded Config prüfen (Kunden-Paket)
        from ce365.setup.embedded_config import is_embedded, get_config
        if is_embedded():
            # Kunden-Paket: Techniker-Info anzeigen, kein Wizard
            _show_embedded_banner(get_config())
        else:
            # 1. Setup-Wizard (falls .env nicht existiert)
            if not run_setup_if_needed():
                print("\n👋 Setup abgebrochen. Auf Wiedersehen!")
                sys.exit(0)

        # 2. Techniker-Passwort prüfen
        if not verify_technician_password():
            sys.exit(1)

        # 3. Bot starten mit Lizenz-Session-Management
        bot = CE365Bot()
        asyncio.run(_run_with_license_session(bot))

    except KeyboardInterrupt:
        print("\n\n👋 Session beendet. Auf Wiedersehen!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Kritischer Fehler: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
