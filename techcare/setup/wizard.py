"""
TechCare Bot - Einrichtungsassistent

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


class SetupWizard:
    """
    Interaktiver Einrichtungsassistent für TechCare Bot

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

        # 2. API Key
        api_key = self._ask_api_key()
        if not api_key:
            return False

        # 3. Use-Case / Briefing (optional)
        briefing = self._ask_briefing()

        # 4. .env erstellen
        self.console.print()
        with self.console.status("[bold green]Erstelle Konfiguration..."):
            success = self._create_env_file(
                user_name=user_name,
                company=company,
                api_key=api_key,
                briefing=briefing
            )

        if not success:
            self.console.print("[red]❌ Fehler beim Erstellen der .env Datei[/red]")
            return False

        # 5. API Key testen (optional)
        self.console.print()
        if Confirm.ask("API Key jetzt testen?", default=True):
            if not self._test_api_key(api_key):
                self.console.print("\n[yellow]⚠️  API Key konnte nicht getestet werden.[/yellow]")
                self.console.print("[yellow]   Du kannst TechCare trotzdem nutzen.[/yellow]")
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
        welcome_text.append("TechCare Bot - Einrichtungsassistent\n\n", style="bold cyan")
        welcome_text.append("Willkommen! ", style="bold")
        welcome_text.append("Lass uns TechCare Bot einrichten.\n")
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

    def _ask_briefing(self) -> str:
        """Fragt nach Use-Case / Briefing (optional)"""
        self.console.print("\n[bold]4. Briefing / Use-Case[/bold] [dim](optional)[/dim]")
        self.console.print("   [dim]Beschreibe kurz wofür du TechCare nutzt[/dim]")
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
        briefing: str
    ) -> bool:
        """
        Erstellt .env Datei aus Template

        Args:
            user_name: Name des Users
            company: Firma/Team
            api_key: Anthropic API Key
            briefing: Use-Case Beschreibung

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

            # User-Info als Kommentar hinzufügen
            header = f"""# ============================================================================
# TechCare Bot - Konfiguration
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
        success_text.append("TechCare Bot ist jetzt einsatzbereit.\n\n")
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
