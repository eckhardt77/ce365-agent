"""
CE365 Agent — Kunden-Paket-Generator

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Generiert portable Kunden-Binaries (.exe / macOS Binary)
mit eingebetteter Techniker-Konfiguration.

Usage:
    ce365 --generate-package
"""

import os
import sys
import shutil
import base64
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text


console = Console()


class PackageGenerator:
    """Generiert portable Kunden-Pakete mit eingebetteter Config"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.env_path = self.project_root / ".env"
        self.embedded_config_path = (
            self.project_root / "ce365" / "setup" / "embedded_config.py"
        )
        self.spec_path = self.project_root / "ce365.spec"
        self.dist_dir = self.project_root / "dist"

    def run(self) -> bool:
        """
        Hauptprozess: Kunden-Paket generieren

        Returns:
            True wenn erfolgreich
        """
        console.print()
        console.print(
            Panel(
                "[bold cyan]CE365 Agent — Kunden-Paket-Generator[/bold cyan]\n\n"
                "Erstellt eine portable Binary mit deiner Konfiguration.\n"
                "Kunden brauchen kein Python und keinen Setup-Wizard.",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        console.print()

        # 0. Edition prüfen — nur Pro darf Kunden-Pakete erstellen
        try:
            from ce365.config import settings as settings_module
            settings_module._settings = None  # Singleton zurücksetzen
            settings = settings_module.get_settings()
            if settings.edition != "pro":
                console.print("[red]❌ Kunden-Paket-Generator ist nur in der Pro Edition verfügbar.[/red]")
                console.print("[dim]Upgrade auf Pro: https://agent.ce365.de/#preise[/dim]\n")
                return False
        except Exception:
            pass  # Wenn Settings nicht laden → Prerequisites-Check greift

        # 1. Voraussetzungen prüfen
        if not self._check_prerequisites():
            return False

        # 2. Techniker-Config lesen
        config = self._read_technician_config()
        if not config:
            return False

        # 3. Config anzeigen und bestätigen
        self._show_config_summary(config)
        if not Confirm.ask("\nMit dieser Konfiguration fortfahren?", default=True):
            console.print("\n[yellow]Abgebrochen.[/yellow]")
            return False

        # 4. Embedded Config schreiben
        console.print()
        if not self._write_embedded_config(config):
            return False

        # 5. PyInstaller Build
        success = self._run_build()

        # 6. Embedded Config zurücksetzen (Sicherheit!)
        self._reset_embedded_config()

        if success:
            self._show_success()

        return success

    def _check_prerequisites(self) -> bool:
        """Prüft ob alle Voraussetzungen erfüllt sind"""
        errors = []

        # .env vorhanden?
        if not self.env_path.exists():
            errors.append(
                "Keine .env Datei gefunden. Führe zuerst 'ce365' aus "
                "um den Setup-Wizard zu durchlaufen."
            )

        # PyInstaller installiert?
        try:
            import PyInstaller  # noqa: F401
        except ImportError:
            errors.append(
                "PyInstaller nicht installiert. Installiere mit:\n"
                "   pip install -r requirements-build.txt"
            )

        # ce365.spec vorhanden?
        if not self.spec_path.exists():
            errors.append(f"ce365.spec nicht gefunden unter {self.spec_path}")

        if errors:
            console.print("[red]Voraussetzungen nicht erfüllt:[/red]\n")
            for err in errors:
                console.print(f"  [red]•[/red] {err}")
            console.print()
            return False

        return True

    def _read_technician_config(self) -> Optional[dict]:
        """Liest Techniker-Konfiguration aus .env"""
        try:
            config = {}
            with open(self.env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        config[key.strip()] = value.strip()

            # Pflichtfelder prüfen
            required = ["ANTHROPIC_API_KEY"]
            # Mindestens ein API-Key muss vorhanden sein
            provider = config.get("LLM_PROVIDER", "anthropic")
            key_map = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
            }
            required_key = key_map.get(provider, "ANTHROPIC_API_KEY")

            if not config.get(required_key):
                console.print(
                    f"[red]Kein API-Key für Provider '{provider}' "
                    f"in .env gefunden.[/red]"
                )
                return None

            return config

        except Exception as e:
            console.print(f"[red]Fehler beim Lesen der .env: {e}[/red]")
            return None

    def _show_config_summary(self, config: dict):
        """Zeigt Zusammenfassung der Konfiguration"""
        # Techniker-Info aus .env-Kommentaren lesen
        tech_name = "Techniker"
        company = ""
        try:
            with open(self.env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("# User:"):
                        tech_name = line.split(":", 1)[1].strip()
                    elif line.startswith("# Firma:"):
                        company = line.split(":", 1)[1].strip()
        except Exception:
            pass

        provider = config.get("LLM_PROVIDER", "anthropic")
        edition = config.get("EDITION", "community")
        has_password = bool(config.get("TECHNICIAN_PASSWORD_HASH"))
        has_license = bool(config.get("LICENSE_KEY"))

        summary = Text()
        summary.append("Konfiguration für Kunden-Paket:\n\n", style="bold")
        summary.append(f"  Techniker:    {tech_name}\n")
        if company:
            summary.append(f"  Firma:        {company}\n")
        summary.append(f"  Edition:      {edition.title()}\n")
        summary.append(f"  Provider:     {provider.title()}\n")
        summary.append(f"  API-Key:      {'***' + config.get(
            {
                'anthropic': 'ANTHROPIC_API_KEY',
                'openai': 'OPENAI_API_KEY',
                'openrouter': 'OPENROUTER_API_KEY',
            }.get(provider, 'ANTHROPIC_API_KEY'), ''
        )[-8:]}\n")
        summary.append(f"  Lizenz:       {'Ja' if has_license else 'Nein'}\n")
        summary.append(f"  Passwort:     {'Gesetzt' if has_password else 'NICHT gesetzt!'}\n")

        if not has_password:
            summary.append(
                "\n  [yellow]WARNUNG: Ohne Passwort kann jeder die Binary starten![/yellow]",
                style="yellow",
            )

        console.print(Panel(summary, border_style="cyan", padding=(1, 2)))

    def _write_embedded_config(self, config: dict) -> bool:
        """Schreibt die eingebettete Config in embedded_config.py"""
        try:
            # API-Key leicht obfuskieren (Base64 — kein echter Schutz,
            # aber verhindert einfaches Strings-Dumpen)
            obfuscated_config = {}
            sensitive_keys = [
                "ANTHROPIC_API_KEY",
                "OPENAI_API_KEY",
                "OPENROUTER_API_KEY",
                "LICENSE_KEY",
                "LEARNING_DB_URL",
            ]

            for key, value in config.items():
                if key in sensitive_keys and value:
                    obfuscated_config[key] = base64.b64encode(
                        value.encode()
                    ).decode()
                else:
                    obfuscated_config[key] = value

            # Techniker-Info aus Kommentaren
            tech_name = "Techniker"
            company = ""
            try:
                with open(self.env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("# User:"):
                            tech_name = line.split(":", 1)[1].strip()
                        elif line.startswith("# Firma:"):
                            company = line.split(":", 1)[1].strip()
            except Exception:
                pass

            obfuscated_config["_TECHNICIAN_NAME"] = tech_name
            obfuscated_config["_COMPANY"] = company
            obfuscated_config["_SENSITIVE_KEYS"] = sensitive_keys

            # embedded_config.py schreiben
            content = f'''"""
CE365 Agent — Embedded Config (generiert)

ACHTUNG: Diese Datei wird automatisch generiert und enthält
Techniker-Konfiguration. Nicht manuell bearbeiten!
"""

EMBEDDED = True

CONFIG = {repr(obfuscated_config)}


def is_embedded() -> bool:
    """Prüft ob diese Binary ein eingebettetes Kunden-Paket ist"""
    return EMBEDDED and bool(CONFIG)


def get_config() -> dict:
    """Gibt die eingebettete Konfiguration zurück (deobfuskiert)"""
    import base64
    if not is_embedded():
        return {{}}
    result = CONFIG.copy()
    sensitive = result.pop("_SENSITIVE_KEYS", [])
    for key in sensitive:
        if key in result and result[key]:
            try:
                result[key] = base64.b64decode(result[key]).decode()
            except Exception:
                pass
    return result
'''

            self.embedded_config_path.write_text(content, encoding="utf-8")

            with console.status("[bold green]Embedded Config geschrieben..."):
                pass
            console.print("[green]✓ Embedded Config erstellt[/green]")
            return True

        except Exception as e:
            console.print(f"[red]Fehler beim Schreiben der Embedded Config: {e}[/red]")
            return False

    def _reset_embedded_config(self):
        """Setzt embedded_config.py auf den Default zurück (Sicherheit)"""
        try:
            default_content = '''"""
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
'''
            self.embedded_config_path.write_text(default_content, encoding="utf-8")
            console.print("[green]✓ Embedded Config zurückgesetzt[/green]")
        except Exception as e:
            console.print(
                f"[yellow]⚠ Embedded Config konnte nicht zurückgesetzt werden: {e}[/yellow]\n"
                f"[yellow]  Bitte manuell prüfen: {self.embedded_config_path}[/yellow]"
            )

    def _run_build(self) -> bool:
        """Führt PyInstaller Build aus"""
        try:
            console.print()
            with console.status(
                "[bold green]Baue Kunden-Paket mit PyInstaller... "
                "(das kann 1-2 Minuten dauern)"
            ):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "PyInstaller",
                        str(self.spec_path),
                        "--noconfirm",
                        "--clean",
                    ],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

            if result.returncode != 0:
                console.print("[red]PyInstaller Build fehlgeschlagen:[/red]")
                # Nur die letzten 20 Zeilen der Fehlerausgabe zeigen
                error_lines = result.stderr.strip().split("\n")
                for line in error_lines[-20:]:
                    console.print(f"  [dim]{line}[/dim]")
                return False

            console.print("[green]✓ PyInstaller Build erfolgreich[/green]")
            return True

        except FileNotFoundError:
            console.print(
                "[red]PyInstaller nicht gefunden. Installiere mit:[/red]\n"
                "   pip install -r requirements-build.txt"
            )
            return False
        except subprocess.TimeoutExpired:
            console.print("[red]Build-Timeout (>10 Minuten). Abgebrochen.[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Build-Fehler: {e}[/red]")
            return False

    def _show_success(self):
        """Zeigt Erfolgs-Nachricht"""
        # Output-Datei finden
        if sys.platform == "win32":
            binary_name = "ce365.exe"
        else:
            binary_name = "ce365"

        binary_path = self.dist_dir / binary_name

        if not binary_path.exists():
            console.print(
                "[yellow]⚠ Binary wurde erstellt, aber nicht am erwarteten Ort gefunden.[/yellow]"
            )
            return

        size_mb = binary_path.stat().st_size / (1024 * 1024)

        success_text = Text()
        success_text.append("Kunden-Paket erfolgreich erstellt!\n\n", style="bold green")
        success_text.append(f"  Datei:    {binary_path}\n")
        success_text.append(f"  Größe:    {size_mb:.1f} MB\n\n")
        success_text.append("Nächste Schritte:\n", style="bold")
        success_text.append("  1. Kopiere die Datei auf Kunden-PCs (USB, NAS, Cloud)\n")
        success_text.append("  2. Rechtsklick → 'Als Administrator ausführen'\n")
        success_text.append("  3. Techniker-Passwort eingeben → Bot startet\n")

        console.print()
        console.print(Panel(success_text, border_style="green", padding=(1, 2)))
        console.print()


def run_generate_package() -> bool:
    """Entry Point für ce365 --generate-package"""
    generator = PackageGenerator()
    return generator.run()
