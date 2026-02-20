"""
CE365 Agent - AI-powered IT Maintenance Assistant

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License
"""

import asyncio
import atexit
import signal
import sys
import argparse
import shutil
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
import bcrypt
from ce365.core.bot import CE365Bot
from ce365.setup.wizard import run_setup_if_needed
from ce365.config.settings import get_settings
from ce365.core.health import run_health_check


console = Console()


def _show_portable_banner():
    """Zeigt Techniker-Info beim Start einer portablen Kunden-Binary"""
    from ce365.__version__ import __version__
    from rich.panel import Panel
    from rich.text import Text

    settings = get_settings()
    tech_name = settings.technician_name or "Techniker"
    company = settings.company or ""
    edition = settings.edition.title()

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

        # 3 Versuche
        for attempt in range(3):
            password = Prompt.ask("Passwort", password=True)

            if bcrypt.checkpw(password.encode("utf-8"), settings.technician_password_hash.encode("utf-8")):
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
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

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


def _check_and_offer_update():
    """
    Prüft ob ein Update verfügbar ist und bietet es dem Techniker an.
    Nur für portable Binaries — zeigt Hinweis, Techniker entscheidet.
    """
    if not getattr(sys, "frozen", False):
        return  # Nur für Binaries

    try:
        from ce365.__version__ import __version__
        from ce365.core.updater import check_for_update

        update_info = check_for_update(__version__)
        if not update_info or not update_info.get("update_available"):
            return

        latest = update_info.get("latest_version", "?")
        console.print(
            f"[bold yellow]Update verfügbar: v{__version__} → v{latest}[/bold yellow]"
        )

        if Confirm.ask("Jetzt updaten?", default=False):
            from ce365.core.updater import _download_binary, _replace_binary
            settings = get_settings()

            console.print("[dim]Lade Update herunter...[/dim]")
            download_url = update_info.get("download_url", "")
            tmp_path = _download_binary(settings.license_key, download_url)

            if tmp_path:
                console.print("[dim]Installiere Update...[/dim]")
                if _replace_binary(tmp_path):
                    console.print(
                        f"\n[green]Update auf v{latest} erfolgreich![/green]"
                    )
                    console.print("[dim]Bitte CE365 neu starten.[/dim]\n")
                    sys.exit(0)
                else:
                    console.print("[red]Update fehlgeschlagen. Weiter mit aktueller Version.[/red]\n")
            else:
                console.print("[red]Download fehlgeschlagen. Weiter mit aktueller Version.[/red]\n")
        else:
            console.print("[dim]Update übersprungen — weiter mit aktueller Version.[/dim]\n")

    except Exception:
        pass  # Update-Check soll nie den Start blockieren


_active_session_manager = None


def _sync_release_session():
    """Notfall-Release falls async finally nicht greift"""
    mgr = _active_session_manager
    if mgr and mgr.session_token:
        try:
            import httpx
            settings = get_settings()
            httpx.post(
                f"{settings.license_server_url}/api/license/session/release",
                json={"session_token": mgr.session_token},
                timeout=3,
            )
        except Exception:
            pass


def _signal_handler(signum, frame):
    _sync_release_session()
    sys.exit(0)


atexit.register(_sync_release_session)
signal.signal(signal.SIGTERM, _signal_handler)


async def _run_with_license_session(bot):
    """
    Führt den Bot mit Lizenz-Session-Management aus

    - Startet Session beim Lizenzserver (Pro)
    - Heartbeats alle 5 Minuten
    - Session-Release beim Beenden
    """
    global _active_session_manager
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
                _active_session_manager = session_manager
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
            _active_session_manager = None


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
        "--verbose",
        action="store_true",
        help="Zeigt Details bei --health/--selftest (jedes Tool/Modul einzeln)"
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Integrations-Selftest (fuehrt Tools, PDF, DB, LLM tatsaechlich aus)"
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
        from ce365.__version__ import __version__
        mode = "Binary" if getattr(sys, "frozen", False) else "pip"
        try:
            edition = get_settings().edition.title()
        except Exception:
            edition = "Community"
        print(f"CE365 Agent v{__version__} ({edition} Edition, {mode})")
        return

    if args.health:
        exit_code = run_health_check(verbose=args.verbose)
        sys.exit(exit_code)

    if args.selftest:
        from ce365.core.selftest import run_selftest
        exit_code = run_selftest(verbose=args.verbose)
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
        if getattr(sys, "frozen", False):
            console.print("\n[yellow]⚠ Kunden-Paket-Generator ist nur über die pip-Installation verfügbar.[/yellow]")
            console.print("[dim]Auf dem Techniker-PC: pip3 install ce365-agent && ce365 --generate-package[/dim]\n")
            sys.exit(1)
        settings = get_settings()
        if settings.edition != "pro":
            console.print("\n[red]❌ Kunden-Paket-Generator ist nur in der Pro Edition verfügbar.[/red]")
            console.print("[dim]Upgrade auf Pro: https://agent.ce365.de/#preise[/dim]\n")
            sys.exit(1)
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
        # Portable Binary prüfen (Kunden-Paket)
        is_portable = False
        try:
            settings = get_settings()
            is_portable = settings.is_portable()
        except (ValueError, Exception):
            pass  # Keine gültige Config → Wizard wird gestartet

        if is_portable:
            # Kunden-Paket: Techniker-Info anzeigen, kein Wizard
            _show_portable_banner()
            # Update-Check anbieten
            _check_and_offer_update()
        else:
            # 1. Setup-Wizard (falls .env nicht existiert)
            if not run_setup_if_needed():
                print("\n👋 Setup abgebrochen. Auf Wiedersehen!")
                sys.exit(0)

            # Settings-Singleton zurücksetzen (Wizard hat .env erstellt/geändert)
            from ce365.config import settings as settings_module
            settings_module._settings = None

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
