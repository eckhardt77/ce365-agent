"""
CE365 Agent - Einrichtungsassistent

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

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
from passlib.context import CryptContext


class SetupWizard:
    """
    Interaktiver Einrichtungsassistent für CE365 Agent

    Führt durch Initial-Setup wenn .env nicht existiert
    """

    def __init__(self):
        self.console = Console()
        self.env_path = Path(".env")
        self.env_example_path = Path(".env.example")

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

        # 3. API Key
        api_key = self._ask_api_key()
        if not api_key:
            return False

        # 4. Lizenzschlüssel (für Pro/Enterprise) - ERFORDERLICH
        license_key = ""
        if edition in ["pro", "business"]:
            license_key = self._ask_license_key()
            if not license_key:
                return False

        # 5. Netzwerkverbindung (für Remote Services) - ERFORDERLICH
        network_config = {}
        if edition == "business":
            network_config = self._ask_network_connection()
            if network_config is None:
                return False

        # 6. Learning Database (nur für Business) - ERFORDERLICH
        db_config = {}
        if edition == "business":
            db_config = self._ask_database()
            if db_config is None:  # User abgebrochen
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
                api_key=api_key,
                briefing=briefing,
                edition=edition,
                license_key=license_key,
                network_config=network_config,
                db_config=db_config,
                technician_password=technician_password
            )

        if not success:
            self.console.print("[red]❌ Fehler beim Erstellen der .env Datei[/red]")
            return False

        # 5. API Key testen (optional)
        self.console.print()
        if Confirm.ask("API Key jetzt testen?", default=True):
            if not self._test_api_key(api_key):
                self.console.print("\n[yellow]⚠️  API Key konnte nicht getestet werden.[/yellow]")
                self.console.print("[yellow]   Du kannst CE365 trotzdem nutzen.[/yellow]")
                if not Confirm.ask("\nTrotzdem fortfahren?", default=True):
                    return False

        # 6. Success!
        self._show_success(user_name)

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

        self.console.print("   [cyan]1[/cyan] Free (kostenlos, Basis-Diagnose, 5 Remediation Runs/Monat)")
        self.console.print("   [cyan]2[/cyan] Pro (€49/Seat/Monat, alle Tools, bis 10 Systeme)")
        self.console.print("   [cyan]3[/cyan] Business (€99/Seat/Monat, ∞ Systeme, Monitoring, Team)\n")

        choice = Prompt.ask(
            "   Deine Wahl",
            choices=["1", "2", "3"],
            default="1"
        )

        edition_map = {
            "1": "free",
            "2": "pro",
            "3": "business"
        }

        edition = edition_map[choice]

        # Info für Business
        if edition == "business":
            self.console.print("\n   [yellow]💡 Business benötigt eine gemeinsame Datenbank für das Team-Learning![/yellow]")

        return edition

    def _ask_license_key(self) -> Optional[str]:
        """Fragt nach Lizenzschlüssel (erforderlich)"""
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

            return license_key.strip()

    def _ask_network_connection(self) -> Optional[dict]:
        """Fragt nach Netzwerkverbindung zu Backend-Services"""
        self.console.print("\n[bold]🌐 Netzwerkverbindung[/bold]")
        self.console.print("   [dim]Wie soll CE365 mit dem Backend verbinden?[/dim]\n")

        self.console.print("   [cyan]1[/cyan] Cloudflare Tunnel (empfohlen, automatisches HTTPS)")
        self.console.print("   [cyan]2[/cyan] Tailscale (Zero-Config VPN, Magic DNS)")
        self.console.print("   [cyan]3[/cyan] VPN (WireGuard, OpenVPN, etc.)")
        self.console.print("   [cyan]4[/cyan] Direkte IP/Hostname (LAN oder Port-Forwarding)\n")

        method_choice = Prompt.ask(
            "   Netzwerk-Methode",
            choices=["1", "2", "3", "4"],
            default="1"
        )

        method_map = {
            "1": "cloudflare",
            "2": "tailscale",
            "3": "vpn",
            "4": "direct"
        }

        method = method_map[method_choice]

        # Backend-URL eingeben
        self.console.print(f"\n   [bold]Backend-URL:[/bold]\n")

        if method == "cloudflare":
            self.console.print("   [dim]Beispiel: https://ce365.deinefirma.de[/dim]")
        elif method == "tailscale":
            self.console.print("   [dim]Beispiel: http://ce365 (Magic DNS)[/dim]")
        elif method == "vpn":
            self.console.print("   [dim]Beispiel: http://192.168.1.100[/dim]")
        else:  # direct
            self.console.print("   [dim]Beispiel: http://192.168.1.100 oder https://ce365.firma.de[/dim]")

        backend_url = Prompt.ask("   Backend-URL")

        if not backend_url or backend_url.lower() in ["exit", "quit", "q"]:
            self.console.print("\n[yellow]Setup abgebrochen.[/yellow]")
            return None

        self.console.print("\n   [green]✓ Netzwerk-Konfiguration gespeichert[/green]")

        return {
            "method": method,
            "backend_url": backend_url.strip()
        }

    def _ask_technician_password(self) -> Optional[str]:
        """Fragt nach Techniker-Passwort (bcrypt hash)"""
        self.console.print("\n[bold]🔐 Techniker-Passwort[/bold] [dim](optional aber empfohlen)[/dim]")
        self.console.print("   [dim]Schützt CE365 vor unbefugtem Zugriff[/dim]")
        self.console.print("   [dim]Ohne Passwort kann jeder CE365 starten![/dim]\n")

        if not Confirm.ask("   Passwort jetzt setzen?", default=True):
            return None

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
            password_hash = pwd_context.hash(password)

            self.console.print("\n   [green]✓ Passwort gespeichert[/green]")
            return password_hash

    def _ask_api_key(self) -> Optional[str]:
        """Fragt nach Anthropic API Key"""
        self.console.print("\n[bold]3. Anthropic API Key[/bold] [red](erforderlich)[/red]")
        self.console.print("   [dim]Erstelle einen Key: https://console.anthropic.com[/dim]\n")

        while True:
            api_key = Prompt.ask(
                "   API Key",
                password=True
            )

            if not api_key or api_key.lower() in ["exit", "quit", "q"]:
                self.console.print("\n[yellow]Setup abgebrochen.[/yellow]")
                return None

            # Format-Validierung
            if not api_key.startswith("sk-ant-"):
                self.console.print("\n   [red]❌ Ungültiges Format. API Keys beginnen mit 'sk-ant-'[/red]")
                if not Confirm.ask("   Nochmal versuchen?", default=True):
                    return None
                continue

            return api_key.strip()

    def _ask_database(self) -> Optional[dict]:
        """Fragt nach Datenbank-Konfiguration (Enterprise)"""
        self.console.print("\n[bold]🧠 Shared Learning Database[/bold] [red](Enterprise)[/red]")
        self.console.print("   [dim]Dein Team braucht eine gemeinsame Datenbank.[/dim]")
        self.console.print("   [dim]Jeder Techniker trägt zum kollektiven Wissen bei![/dim]\n")

        self.console.print("   [cyan]1[/cyan] MySQL/MariaDB (empfohlen für Teams)")
        self.console.print("   [cyan]2[/cyan] PostgreSQL")
        self.console.print("   [cyan]3[/cyan] SQLite (nur für Testing/Demo)\n")

        db_choice = Prompt.ask(
            "   Datenbank-Typ",
            choices=["1", "2", "3"],
            default="1"
        )

        db_type_map = {
            "1": "mysql",
            "2": "postgresql",
            "3": "sqlite"
        }

        db_type = db_type_map[db_choice]

        if db_type == "sqlite":
            self.console.print("\n   [yellow]⚠️  SQLite ist NICHT für Teams geeignet![/yellow]")
            self.console.print("   [yellow]   Nutze MySQL oder PostgreSQL für Shared Learning.[/yellow]")

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
        api_key: str,
        briefing: str,
        edition: str = "free",
        license_key: str = "",
        network_config: dict = None,
        db_config: dict = None,
        technician_password: str = None
    ) -> bool:
        """
        Erstellt .env Datei aus Template

        Args:
            user_name: Name des Users
            company: Firma/Team
            api_key: Anthropic API Key
            briefing: Use-Case Beschreibung
            edition: Edition (free/pro/business)
            db_config: Datenbank-Konfiguration (nur Enterprise)

        Returns:
            True wenn erfolgreich
        """
        try:
            # Template laden oder Default verwenden
            if self.env_example_path.exists():
                template = self.env_example_path.read_text()
            else:
                template = self._get_default_template()

            # Platzhalter ersetzen
            config = template.replace(
                "ANTHROPIC_API_KEY=your_api_key_here",
                f"ANTHROPIC_API_KEY={api_key}"
            )

            # Edition hinzufügen
            config = config.replace(
                "EDITION=free",
                f"EDITION={edition}"
            )

            # Lizenzschlüssel hinzufügen
            if license_key:
                config = config.replace(
                    "LICENSE_KEY=",
                    f"LICENSE_KEY={license_key}"
                )

            # Netzwerk-Config hinzufügen
            if network_config:
                config = config.replace(
                    "BACKEND_URL=",
                    f"BACKEND_URL={network_config['backend_url']}"
                )
                config = config.replace(
                    "NETWORK_METHOD=direct",
                    f"NETWORK_METHOD={network_config['method']}"
                )

            # Techniker-Passwort hinzufügen
            if technician_password:
                config = config.replace(
                    "TECHNICIAN_PASSWORD_HASH=",
                    f"TECHNICIAN_PASSWORD_HASH={technician_password}"
                )

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

            return True

        except Exception as e:
            self.console.print(f"\n[red]Fehler: {str(e)}[/red]")
            return False

    def _test_api_key(self, api_key: str) -> bool:
        """
        Testet API Key mit einfachem Request

        Args:
            api_key: API Key zum Testen

        Returns:
            True wenn Key funktioniert
        """
        try:
            with self.console.status("[bold cyan]Teste API Key..."):
                client = Anthropic(api_key=api_key)

                # Einfacher Test-Request (minimal tokens)
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )

                if response.content:
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

    def _get_timestamp(self) -> str:
        """Gibt aktuellen Timestamp zurück"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_default_template(self) -> str:
        """Gibt Default .env Template zurück falls .env.example fehlt"""
        return """# Anthropic API Key (erforderlich)
ANTHROPIC_API_KEY=your_api_key_here

# Optional: Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: Claude Model
CLAUDE_MODEL=claude-sonnet-4-5-20250929

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
