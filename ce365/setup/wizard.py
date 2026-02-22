"""
CE365 Agent - Einrichtungsassistent

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Interaktiver Setup-Wizard für den ersten Start:
- Name & Firma konfigurieren
- API Key einrichten
- .env erstellen
- API Key testen
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from anthropic import Anthropic
import bcrypt


class SetupWizard:
    """
    Interaktiver Einrichtungsassistent für CE365 Agent

    Führt durch Initial-Setup wenn .env nicht existiert
    """

    # Standard-URL für den Lizenzserver
    DEFAULT_LICENSE_SERVER_URL = "https://license.ce365.de"

    def __init__(self):
        self.console = Console()
        if getattr(sys, "frozen", False):
            config_dir = Path(sys.executable).parent / "config"
            config_dir.mkdir(exist_ok=True)
            self.env_path = config_dir / ".env"
        else:
            self.env_path = Path(".env")
        self.env_example_path = Path(".env.example")
        self.license_server_url = self.DEFAULT_LICENSE_SERVER_URL

    def needs_setup(self) -> bool:
        """Prüft ob Setup nötig ist (.env existiert nicht)"""
        return not self.env_path.exists()

    def run(self) -> bool:
        """
        Führt Setup-Wizard aus

        Returns:
            True wenn Setup erfolgreich, False bei Abbruch
        """
        self._show_welcome()

        # 1. Name & Firma
        user_name = self._ask_name()
        if not user_name:
            return False

        company = self._ask_company()

        # 2. Edition
        edition = self._ask_edition()
        self._edition = edition

        # 3. Provider + API Key
        provider, api_key = self._ask_provider()
        if not api_key:
            return False

        # 4. Lizenzschlüssel (für Core/Scale) - ERFORDERLICH
        license_key = ""
        if edition in ("core", "scale"):
            license_key = self._ask_license_key()
            if not license_key:
                return False

        # 5. Learning Database (optional für Core/Scale)
        db_config = {}
        if edition in ("core", "scale"):
            db_config = self._ask_database()
            if db_config is None:
                return False

        # 7. Techniker-Passwort (optional aber empfohlen)
        technician_password = self._ask_technician_password()

        # 8. Use-Case / Briefing (optional)
        briefing = self._ask_briefing()

        # 9. .env erstellen
        self.console.print()
        with self.console.status("[bold green]Erstelle Konfiguration..."):
            success = self._create_env_file(
                user_name=user_name,
                company=company,
                provider=provider,
                api_key=api_key,
                briefing=briefing,
                edition=edition,
                license_key=license_key,
                db_config=db_config,
                technician_password=technician_password
            )

        if not success:
            self.console.print("[red]❌ Fehler beim Erstellen der .env Datei[/red]")
            return False

        # 5. API Key testen (optional)
        self.console.print()
        if Confirm.ask("API Key jetzt testen?", default=True):
            if not self._test_api_key(api_key, provider):
                self.console.print("\n[yellow]⚠️  API Key konnte nicht getestet werden.[/yellow]")
                self.console.print("[yellow]   Du kannst CE365 trotzdem nutzen.[/yellow]")
                if not Confirm.ask("\nTrotzdem fortfahren?", default=True):
                    return False

        # 6. Success!
        self._show_success(user_name)

        # 7. Kunden-Paket generieren? (nur Core/Scale, nur pip-Installation)
        if self._edition in ("core", "scale") and not getattr(sys, "frozen", False):
            self._offer_package_generation()

        return True

    def _show_welcome(self):
        """Zeigt Welcome-Screen"""
        self.console.clear()

        welcome_text = Text()
        welcome_text.append("🔧 ", style="bold cyan")
        welcome_text.append("CE365 Agent - Einrichtungsassistent\n\n", style="bold cyan")
        welcome_text.append("Willkommen! ", style="bold")
        welcome_text.append("Lass uns CE365 Agent einrichten.\n")
        welcome_text.append("Das dauert nur 2 Minuten.", style="dim")

        panel = Panel(
            welcome_text,
            border_style="cyan",
            padding=(1, 2)
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def _ask_name(self) -> Optional[str]:
        """Fragt nach User-Name"""
        self.console.print("[bold]1. Dein Name[/bold]")
        self.console.print("   [dim]Wird für Changelog und Personalisierung verwendet[/dim]\n")

        name = Prompt.ask(
            "   Name",
            default=os.getenv("USER", "Techniker")
        )

        if not name or name.lower() in ["exit", "quit", "q"]:
            self.console.print("\n[yellow]Setup abgebrochen.[/yellow]")
            return None

        return name.strip()

    def _ask_company(self) -> str:
        """Fragt nach Firma/Team (optional)"""
        self.console.print("\n[bold]2. Firma / Team[/bold] [dim](optional)[/dim]")
        self.console.print("   [dim]Für Team-Reports und Identifikation[/dim]\n")

        company = Prompt.ask(
            "   Firma/Team",
            default=""
        )

        return company.strip()

    def _ask_edition(self) -> str:
        """Fragt nach Edition"""
        self.console.print("\n[bold]2. Edition[/bold]")
        self.console.print("   [dim]Welche Edition möchtest du nutzen?[/dim]\n")

        self.console.print("   [cyan]1[/cyan] Free (kostenlos, 11 Diagnose-Tools, 1 Repair, 5 Sessions/Monat)")
        self.console.print("   [cyan]2[/cyan] MSP Core (€99/Seat/Monat, alle 95 Tools, Remote, PDF)")
        self.console.print("   [cyan]3[/cyan] MSP Scale (€199/Seat/Monat, alles aus Core + Team-DB, MCP)\n")

        choice = Prompt.ask(
            "   Deine Wahl",
            choices=["1", "2", "3"],
            default="1"
        )

        edition_map = {
            "1": "free",
            "2": "core",
            "3": "scale",
        }

        return edition_map[choice]

    def _ask_license_key(self) -> Optional[str]:
        """Fragt nach Lizenzschlüssel und validiert online"""
        self.console.print("\n[bold]3a. Lizenzschlüssel[/bold] [red](erforderlich)[/red]")
        self.console.print("   [dim]Erhältlich nach Kauf bei: https://ce365.eckhardt-marketing.de[/dim]")
        self.console.print("   [dim]💡 Für kostenloses Testen: Wähle 'Free Edition' beim Setup[/dim]\n")

        while True:
            license_key = Prompt.ask(
                "   Lizenzschlüssel",
                password=True
            )

            if not license_key or license_key.lower() in ["exit", "quit", "q"]:
                self.console.print("\n[yellow]⚠️  Setup abgebrochen.[/yellow]")
                self.console.print("   [dim]Tipp: Starte Setup neu und wähle 'Free Edition' für kostenloses Testen[/dim]")
                return None

            # Format-Validierung (CE365-EDITION-...)
            if not license_key.startswith("CE365-"):
                self.console.print("\n   [red]❌ Ungültiges Format. Lizenzschlüssel beginnen mit 'CE365-'[/red]")
                if not Confirm.ask("   Nochmal versuchen?", default=True):
                    return None
                continue

            # Online-Validierung gegen Lizenzserver
            license_key = license_key.strip()
            validation = self._validate_license_online(license_key)

            if validation is None:
                # Server nicht erreichbar — User entscheiden lassen
                self.console.print("\n   [yellow]⚠️  Lizenzserver nicht erreichbar.[/yellow]")
                self.console.print("   [dim]Die Lizenz wird beim nächsten Start online geprüft.[/dim]")
                if Confirm.ask("   Trotzdem fortfahren?", default=True):
                    return license_key
                if not Confirm.ask("   Nochmal versuchen?", default=True):
                    return None
                continue

            if validation.get("valid"):
                customer = validation.get("customer_name", "")
                edition = validation.get("edition", "core")
                self.console.print(f"\n   [green]✓ Lizenz gültig! ({edition.title()})[/green]")
                if customer:
                    self.console.print(f"   [dim]Registriert auf: {customer}[/dim]")
                return license_key
            else:
                error = validation.get("error", "Unbekannter Fehler")
                self.console.print(f"\n   [red]❌ Lizenz ungültig: {error}[/red]")
                if not Confirm.ask("   Nochmal versuchen?", default=True):
                    return None
                continue

    def _validate_license_online(self, license_key: str) -> Optional[dict]:
        """
        Validiert Lizenzschlüssel online gegen den Lizenzserver

        Returns:
            Dict mit Validierungsergebnis, oder None wenn Server nicht erreichbar
        """
        from ce365.core.license import validate_license_sync

        license_server_url = self.license_server_url

        with self.console.status("[bold cyan]   Prüfe Lizenzschlüssel..."):
            result = validate_license_sync(license_key, license_server_url)

        # Server nicht erreichbar?
        if not result.get("valid") and "nicht erreichbar" in result.get("error", ""):
            return None

        return result

    def _ask_provider(self) -> tuple:
        """Fragt nach LLM Provider und API Key"""
        self.console.print("\n[bold]3. LLM Provider[/bold]")
        self.console.print("   [dim]Welchen KI-Provider möchtest du nutzen? (BYOK)[/dim]\n")

        self.console.print("   [cyan]1[/cyan] Anthropic (Claude) — empfohlen")
        self.console.print("   [cyan]2[/cyan] OpenAI (GPT-4o)")
        self.console.print("   [cyan]3[/cyan] OpenRouter (viele Modelle)\n")

        choice = Prompt.ask(
            "   Deine Wahl",
            choices=["1", "2", "3"],
            default="1"
        )

        provider_map = {
            "1": "anthropic",
            "2": "openai",
            "3": "openrouter",
        }

        provider = provider_map[choice]

        # API Key abfragen
        key_info = {
            "anthropic": ("Anthropic API Key", "https://console.anthropic.com", "sk-ant-"),
            "openai": ("OpenAI API Key", "https://platform.openai.com/api-keys", "sk-"),
            "openrouter": ("OpenRouter API Key", "https://openrouter.ai/keys", "sk-or-"),
        }

        label, url, prefix = key_info[provider]

        self.console.print(f"\n[bold]   {label}[/bold] [red](erforderlich)[/red]")
        self.console.print(f"   [dim]Erstelle einen Key: {url}[/dim]\n")

        while True:
            api_key = Prompt.ask("   API Key", password=True)

            if not api_key or api_key.lower() in ["exit", "quit", "q"]:
                self.console.print("\n[yellow]Setup abgebrochen.[/yellow]")
                return provider, None

            if not api_key.startswith(prefix):
                self.console.print(f"\n   [red]❌ Ungültiges Format. Keys beginnen mit '{prefix}'[/red]")
                if not Confirm.ask("   Nochmal versuchen?", default=True):
                    return provider, None
                continue

            return provider, api_key.strip()

    def _ask_technician_password(self) -> Optional[str]:
        """Fragt nach Techniker-Passwort (bcrypt hash)"""
        self.console.print("\n[bold]🔐 Techniker-Passwort[/bold] [dim](optional aber empfohlen)[/dim]")
        self.console.print("   [dim]Schützt CE365 vor unbefugtem Zugriff[/dim]")
        self.console.print("   [dim]Ohne Passwort kann jeder CE365 starten![/dim]\n")

        if not Confirm.ask("   Passwort jetzt setzen?", default=True):
            return None

        while True:
            password = Prompt.ask("   Passwort", password=True)

            if not password:
                self.console.print("\n   [yellow]Kein Passwort gesetzt.[/yellow]")
                return None

            if len(password) < 6:
                self.console.print("\n   [red]❌ Passwort zu kurz (min. 6 Zeichen)[/red]")
                continue

            # Bestätigung
            confirm = Prompt.ask("   Passwort wiederholen", password=True)

            if password != confirm:
                self.console.print("\n   [red]❌ Passwörter stimmen nicht überein[/red]")
                continue

            # Hash erstellen
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            self.console.print("\n   [green]✓ Passwort gespeichert[/green]")
            return password_hash

    def _ask_database(self) -> Optional[dict]:
        """Fragt nach Datenbank-Konfiguration (Pro)"""
        self.console.print("\n[bold]🧠 Shared Learning Database[/bold] [dim](optional)[/dim]")
        self.console.print("   [dim]Shared Learning ermöglicht Team-Wissensdatenbank.[/dim]")
        self.console.print("   [dim]Ohne DB wird lokales SQLite verwendet.[/dim]\n")

        self.console.print("   [cyan]1[/cyan] SQLite (lokal, Standard)")
        self.console.print("   [cyan]2[/cyan] PostgreSQL (empfohlen für Teams)")
        self.console.print("   [cyan]3[/cyan] MySQL/MariaDB\n")

        db_choice = Prompt.ask(
            "   Datenbank-Typ",
            choices=["1", "2", "3"],
            default="1"
        )

        db_type_map = {
            "1": "sqlite",
            "2": "postgresql",
            "3": "mysql",
        }

        db_type = db_type_map[db_choice]

        if db_type == "sqlite":
            return {
                "type": "sqlite",
                "url": ""
            }

        # MySQL/PostgreSQL Verbindung konfigurieren
        self.console.print(f"\n   [bold]{db_type.upper()} Verbindungs-Details:[/bold]\n")

        host = Prompt.ask("   Host", default="localhost")
        port = Prompt.ask("   Port", default="3306" if db_type == "mysql" else "5432")
        database = Prompt.ask("   Database Name", default="ce365_learning")
        user = Prompt.ask("   Username", default="ce365")
        password = Prompt.ask("   Password", password=True)

        # Connection String erstellen
        if db_type == "mysql":
            db_url = f"mysql+asyncmy://{user}:{password}@{host}:{port}/{database}"
        else:  # postgresql
            db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

        self.console.print("\n   [green]✓ Datenbank-Konfiguration gespeichert[/green]")
        self.console.print("   [dim]Verbindung wird beim ersten Start getestet[/dim]")

        return {
            "type": db_type,
            "url": db_url
        }

    def _ask_briefing(self) -> str:
        """Fragt nach Use-Case / Briefing (optional)"""
        self.console.print("\n[bold]5. Briefing / Use-Case[/bold] [dim](optional)[/dim]")
        self.console.print("   [dim]Beschreibe kurz wofür du CE365 nutzt[/dim]")
        self.console.print("   [dim]Beispiel: 'Windows-Support für 50 Clients'[/dim]\n")

        briefing = Prompt.ask(
            "   Briefing",
            default=""
        )

        return briefing.strip()

    def _create_env_file(
        self,
        user_name: str,
        company: str,
        provider: str = "anthropic",
        api_key: str = "",
        briefing: str = "",
        edition: str = "free",
        license_key: str = "",
        db_config: dict = None,
        technician_password: str = None,
        license_server_url: str = ""
    ) -> bool:
        """
        Erstellt .env Datei aus Template

        Args:
            user_name: Name des Users
            company: Firma/Team
            provider: LLM Provider (anthropic/openai/openrouter)
            api_key: API Key für den gewählten Provider
            briefing: Use-Case Beschreibung
            edition: Edition (free/core/scale)
            db_config: Datenbank-Konfiguration (optional, Core/Scale)

        Returns:
            True wenn erfolgreich
        """
        try:
            # Template laden oder Default verwenden
            if self.env_example_path.exists():
                template = self.env_example_path.read_text()
            else:
                template = self._get_default_template()

            # Provider + API Key setzen
            config = template.replace(
                "LLM_PROVIDER=anthropic",
                f"LLM_PROVIDER={provider}"
            )

            # API Key für den richtigen Provider setzen
            key_env_map = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
            }
            key_var = key_env_map.get(provider, "ANTHROPIC_API_KEY")
            if key_var == "ANTHROPIC_API_KEY":
                config = config.replace(
                    "ANTHROPIC_API_KEY=your_api_key_here",
                    f"ANTHROPIC_API_KEY={api_key}"
                )
            else:
                config = config.replace(
                    f"{key_var}=",
                    f"{key_var}={api_key}"
                )

            # Edition hinzufügen
            config = config.replace(
                "EDITION=community",
                f"EDITION={edition}"
            )

            # Lizenzschlüssel hinzufügen
            if license_key:
                config = config.replace(
                    "LICENSE_KEY=",
                    f"LICENSE_KEY={license_key}"
                )

            # Techniker-Passwort hinzufügen
            if technician_password:
                config = config.replace(
                    "TECHNICIAN_PASSWORD_HASH=",
                    f"TECHNICIAN_PASSWORD_HASH={technician_password}"
                )

            # License Server URL hinzufügen
            server_url = license_server_url or self.license_server_url
            if "LICENSE_SERVER_URL=" in config:
                config = config.replace(
                    "LICENSE_SERVER_URL=",
                    f"LICENSE_SERVER_URL={server_url}"
                )
            else:
                config += f"\n# License Server\nLICENSE_SERVER_URL={server_url}\n"

            # Datenbank-Config hinzufügen (Enterprise)
            if db_config:
                config = config.replace(
                    'LEARNING_DB_TYPE=sqlite',
                    f'LEARNING_DB_TYPE={db_config["type"]}'
                )
                if db_config["url"]:
                    config = config.replace(
                        'LEARNING_DB_URL=',
                        f'LEARNING_DB_URL={db_config["url"]}'
                    )

            # Techniker-Name und Firma als env-Variablen hinzufügen
            config += f"\n# Techniker\nTECHNICIAN_NAME={user_name}\n"
            if company:
                config += f"COMPANY={company}\n"

            # User-Info als Kommentar hinzufügen
            header = f"""# ============================================================================
# CE365 Agent - Konfiguration
# ============================================================================
# User: {user_name}
"""
            if company:
                header += f"# Firma: {company}\n"
            if briefing:
                header += f"# Use-Case: {briefing}\n"

            header += f"""# Erstellt: {self._get_timestamp()}
# ============================================================================

"""

            config = header + config

            # .env schreiben
            self.env_path.write_text(config)

            # Permissions setzen (nur Owner kann lesen/schreiben)
            os.chmod(self.env_path, 0o600)

            # Bei sudo: Ownership auf echten User uebertragen
            sudo_user = os.environ.get("SUDO_USER")
            if sudo_user and os.getuid() == 0:
                import pwd
                pw = pwd.getpwnam(sudo_user)
                os.chown(self.env_path, pw.pw_uid, pw.pw_gid)
                os.chown(self.env_path.parent, pw.pw_uid, pw.pw_gid)

            return True

        except Exception as e:
            self.console.print(f"\n[red]Fehler: {str(e)}[/red]")
            return False

    def _test_api_key(self, api_key: str, provider: str = "anthropic") -> bool:
        """
        Testet API Key mit einfachem Request

        Args:
            api_key: API Key zum Testen
            provider: LLM Provider (anthropic/openai/openrouter)

        Returns:
            True wenn Key funktioniert
        """
        try:
            with self.console.status("[bold cyan]Teste API Key..."):
                if provider == "anthropic":
                    client = Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model="claude-sonnet-4-5-20250929",
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                    if response.content:
                        self.console.print("\n[green]✓ API Key funktioniert![/green]")
                        return True

                elif provider == "openai":
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                    if response.choices:
                        self.console.print("\n[green]✓ API Key funktioniert![/green]")
                        return True

                elif provider == "openrouter":
                    from openai import OpenAI
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://openrouter.ai/api/v1"
                    )
                    response = client.chat.completions.create(
                        model="openai/gpt-4o-mini",
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                    if response.choices:
                        self.console.print("\n[green]✓ API Key funktioniert![/green]")
                        return True

        except Exception as e:
            self.console.print(f"\n[red]❌ API Key Test fehlgeschlagen: {str(e)}[/red]")
            return False

    def _show_success(self, user_name: str):
        """Zeigt Success-Screen"""
        self.console.print()

        success_text = Text()
        success_text.append("✅ ", style="bold green")
        success_text.append("Setup abgeschlossen!\n\n", style="bold green")
        success_text.append(f"Willkommen, {user_name}! ", style="bold")
        success_text.append("CE365 Agent ist jetzt einsatzbereit.\n\n")
        success_text.append("Starte mit: ", style="dim")
        success_text.append("Neuer Fall", style="bold cyan")

        panel = Panel(
            success_text,
            border_style="green",
            padding=(1, 2)
        )

        self.console.print(panel)
        self.console.print()

    def _offer_package_generation(self):
        """Bietet an, ein Kunden-Paket zu generieren"""
        self.console.print("\n[bold]Kunden-Paket generieren?[/bold]")
        self.console.print(
            "   [dim]Erstelle eine portable .exe/.app die du auf Kunden-PCs "
            "kopieren kannst.[/dim]"
        )
        self.console.print(
            "   [dim]Kunden brauchen kein Python und keinen Setup-Wizard.[/dim]\n"
        )

        if Confirm.ask("   Jetzt Kunden-Paket generieren?", default=False):
            try:
                from ce365.setup.package_generator import run_generate_package
                run_generate_package()
            except ImportError:
                self.console.print(
                    "\n   [yellow]⚠ Package-Generator nicht verfügbar.[/yellow]"
                )
                self.console.print(
                    "   [dim]Installiere Build-Tools: "
                    "pip install -r requirements-build.txt[/dim]"
                )
            except Exception as e:
                self.console.print(
                    f"\n   [red]Fehler: {e}[/red]"
                )
        else:
            self.console.print(
                "\n   [dim]Du kannst später jederzeit 'ce365 --generate-package' "
                "ausführen.[/dim]\n"
            )

    def _get_timestamp(self) -> str:
        """Gibt aktuellen Timestamp zurück"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_default_template(self) -> str:
        """Gibt Default .env Template zurück falls .env.example fehlt"""
        return """# LLM Provider (anthropic, openai, openrouter)
LLM_PROVIDER=anthropic

# Anthropic API Key (erforderlich)
ANTHROPIC_API_KEY=your_api_key_here

# OpenAI API Key (falls OpenAI als Provider)
OPENAI_API_KEY=

# OpenRouter API Key (falls OpenRouter als Provider)
OPENROUTER_API_KEY=

# Edition (community, pro)
EDITION=community

# Lizenzschlüssel (erforderlich für Pro)
LICENSE_KEY=

# Techniker-Passwort (bcrypt hash)
TECHNICIAN_PASSWORD_HASH=

# License Server URL
LICENSE_SERVER_URL=

# Optional: Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: LLM Model (leer = Provider-Default)
LLM_MODEL=

# ============================================================================
# LEARNING SYSTEM - DATABASE KONFIGURATION
# ============================================================================

# Database Type: "sqlite" (lokal) oder "postgresql" (remote)
LEARNING_DB_TYPE=sqlite

# PostgreSQL URL (nur wenn LEARNING_DB_TYPE=postgresql)
LEARNING_DB_URL=

# Lokaler Fallback
LEARNING_DB_FALLBACK=data/cases.db

# Connection Timeout in Sekunden
LEARNING_DB_TIMEOUT=5

# Anzahl Retry-Versuche bei Connection-Fehler
LEARNING_DB_RETRY=3

# ============================================================================
# SECURITY - PII DETECTION (Presidio)
# ============================================================================

# PII Detection aktivieren (empfohlen für Production!)
PII_DETECTION_ENABLED=true

# Detection Level: "high" (alle PII), "medium" (wichtige), "low" (kritische)
PII_DETECTION_LEVEL=high

# User-Warnings anzeigen wenn PII erkannt wurde
PII_SHOW_WARNINGS=true

# ============================================================================
# RESEARCH - WEB SEARCH (DuckDuckGo)
# ============================================================================

# Web-Suche aktivieren (für Problemlösung-Recherche)
WEB_SEARCH_ENABLED=true
"""


def run_setup_if_needed() -> bool:
    """
    Prüft ob Setup nötig ist und führt ihn aus

    Returns:
        True wenn Setup durchgeführt oder nicht nötig
        False wenn Setup abgebrochen
    """
    wizard = SetupWizard()

    if wizard.needs_setup():
        return wizard.run()

    # Setup nicht nötig
    return True
