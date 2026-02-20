"""
CE365 Agent - Slash Command System

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Dispatcher fuer /command Eingaben im Main-Loop.
"""

import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class SlashCommand:
    """Definition eines Slash-Commands"""
    name: str
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    handler: Callable = None  # async def handler(bot, args: str)


class SlashCommandHandler:
    """Leichtgewichtiger Command-Dispatcher"""

    def __init__(self):
        self._commands: Dict[str, SlashCommand] = {}
        self._alias_map: Dict[str, str] = {}  # alias -> command name
        self._register_defaults()

    def register(self, cmd: SlashCommand):
        """Command registrieren"""
        self._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self._alias_map[alias.lower()] = cmd.name

    def is_command(self, user_input: str) -> bool:
        """Prüft ob Eingabe ein Slash-Command oder Alias ist"""
        stripped = user_input.strip().lower()
        if stripped.startswith("/"):
            return True
        # Bare-word Aliases (stats, privacy, datenschutz, daten)
        first_word = stripped.split()[0] if stripped else ""
        return first_word in self._alias_map

    async def execute(self, user_input: str, bot) -> bool:
        """
        Command ausfuehren.

        Returns:
            True wenn Command behandelt wurde
        """
        stripped = user_input.strip()
        parts = stripped.split(maxsplit=1)
        raw_cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Slash entfernen
        if raw_cmd.startswith("/"):
            raw_cmd = raw_cmd[1:]

        # Bare "/" zeigt interaktives Menue
        if not raw_cmd:
            from rich.prompt import Prompt
            console = bot.console.console
            bot.console.display_separator()
            console.print("[bold]Menue[/bold]\n")
            cmd_list = list(self._commands.values())
            for i, cmd in enumerate(cmd_list, 1):
                console.print(f"  [cyan]{i}[/cyan]  {cmd.description}")
            console.print(f"  [cyan]0[/cyan]  Zurueck\n")
            choices = [str(i) for i in range(len(cmd_list) + 1)]
            choice = Prompt.ask("  Wahl", choices=choices, default="0")
            idx = int(choice)
            if idx == 0:
                bot.console.display_info("Zurueck zum Chat.")
                return True
            selected = cmd_list[idx - 1]
            if selected.handler:
                await selected.handler(bot, "")
            return True

        # Alias aufloesen
        cmd_name = self._alias_map.get(raw_cmd, raw_cmd)

        cmd = self._commands.get(cmd_name)
        if not cmd:
            bot.console.display_error(
                f"Unbekannter Command: /{raw_cmd}\n"
                f"Tippe /help fuer alle verfuegbaren Commands."
            )
            return True

        if cmd.handler:
            await cmd.handler(bot, args)
        return True

    def get_help_text(self) -> str:
        """Formatierter Hilfetext fuer /help"""
        lines = []
        for cmd in self._commands.values():
            alias_str = ""
            if cmd.aliases:
                alias_str = f"  (auch: {', '.join(cmd.aliases)})"
            lines.append(f"  /{cmd.name:<12} {cmd.description}{alias_str}")
        return "\n".join(lines)

    # ==========================================
    # DEFAULT COMMANDS
    # ==========================================

    def _register_defaults(self):
        """Alle Standard-Commands registrieren"""
        self.register(SlashCommand(
            name="help",
            aliases=["h", "?"],
            description="Alle Commands anzeigen",
            handler=_cmd_help,
        ))
        self.register(SlashCommand(
            name="report",
            aliases=["r"],
            description="Incident Report erstellen (markdown/soap)",
            handler=_cmd_report,
        ))
        self.register(SlashCommand(
            name="provider",
            aliases=["p"],
            description="LLM-Provider anzeigen/wechseln",
            handler=_cmd_provider,
        ))
        self.register(SlashCommand(
            name="model",
            aliases=["m"],
            description="LLM-Modell anzeigen/wechseln",
            handler=_cmd_model,
        ))
        self.register(SlashCommand(
            name="stats",
            aliases=["stats"],
            description="Learning-Statistiken anzeigen",
            handler=_cmd_stats,
        ))
        self.register(SlashCommand(
            name="privacy",
            aliases=["privacy", "datenschutz", "daten"],
            description="Datenschutz-Menue",
            handler=_cmd_privacy,
        ))
        self.register(SlashCommand(
            name="config",
            aliases=["settings", "setup", "cfg"],
            description="Einstellungen anzeigen/aendern",
            handler=_cmd_config,
        ))
        self.register(SlashCommand(
            name="scan",
            aliases=["analyze", "audit", "analyse"],
            description="Vollstaendige System-Analyse starten",
            handler=_cmd_scan,
        ))
        self.register(SlashCommand(
            name="check",
            aliases=["routine", "routines", "pruefung"],
            description="Audit-Routine starten (komplett/sicherheit/performance/wartung)",
            handler=_cmd_check,
        ))
        self.register(SlashCommand(
            name="update",
            aliases=["upgrade"],
            description="CE365 auf neueste Version aktualisieren",
            handler=_cmd_update,
        ))
        self.register(SlashCommand(
            name="rollback",
            aliases=["downgrade"],
            description="Rollback zur vorherigen Version",
            handler=_cmd_rollback,
        ))


# ==========================================
# COMMAND HANDLER FUNCTIONS
# ==========================================

async def _cmd_help(bot, args: str):
    """Alle verfuegbaren Commands anzeigen"""
    bot.console.display_separator()
    bot.console.console.print("[bold]Verfuegbare Commands:[/bold]\n")
    bot.console.console.print(bot.command_handler.get_help_text())
    bot.console.console.print()


async def _cmd_report(bot, args: str):
    """Incident Report on-demand generieren"""
    fmt = args.strip().lower() if args.strip() else None

    # PDF-Shortcut
    if fmt == "pdf":
        await _generate_pdf_report(bot)
        return

    report_tool = bot.tool_registry.get_tool("generate_incident_report")
    if not report_tool:
        bot.console.display_error("Incident Report Tool nicht verfuegbar.")
        return

    if not fmt:
        choice = bot.console.get_input(
            "Report-Format? [M]arkdown / [S]OAP / [P]DF"
        ).strip().lower()
        if choice in ("m", "markdown"):
            fmt = "markdown"
        elif choice in ("s", "soap"):
            fmt = "soap"
        elif choice in ("p", "pdf"):
            await _generate_pdf_report(bot)
            return
        else:
            bot.console.display_info("Abgebrochen.")
            return

    if fmt not in ("markdown", "soap"):
        # Kurzform akzeptieren
        if fmt in ("m",):
            fmt = "markdown"
        elif fmt in ("s",):
            fmt = "soap"
        else:
            bot.console.display_error(
                f"Unbekanntes Format: {fmt}. Verfuegbar: markdown, soap, pdf"
            )
            return

    try:
        with bot.console.show_spinner(f"Erstelle {fmt.upper()} Report"):
            report = await report_tool.execute(
                format=fmt, include_audit_log=True
            )
        bot.console.display_separator()
        bot.console.console.print(report)
    except Exception as e:
        bot.console.display_error(f"Report-Fehler: {e}")


async def _generate_pdf_report(bot):
    """PDF-Report auf Desktop generieren"""
    from ce365.tools.audit.pdf_report import generate_pdf_report
    from ce365.config.settings import get_settings

    settings = get_settings()

    # System-Info sammeln
    system_info_tool = bot.tool_registry.get_tool("get_system_info")
    system_info = ""
    if system_info_tool:
        try:
            with bot.console.show_spinner("Sammle System-Informationen"):
                system_info = await system_info_tool.execute()
        except Exception:
            pass

    report_data = {
        "system_info": system_info,
        "raw_analysis": "System-Report erstellt auf Anfrage.",
    }

    # Changelog-Daten hinzufuegen falls vorhanden
    if bot.changelog.entries:
        repairs = "\n".join(
            f"- {e.get('action', 'N/A')}: {e.get('detail', '')}"
            for e in bot.changelog.entries
        )
        report_data["repairs"] = repairs

    try:
        with bot.console.show_spinner("Erstelle PDF-Report"):
            path = generate_pdf_report(
                report_data=report_data,
                technician=settings.technician_name or "",
                company=settings.company or "",
            )
        bot.console.display_success(f"PDF-Report gespeichert: {path}")
    except Exception as e:
        bot.console.display_error(f"PDF-Fehler: {e}")


async def _cmd_provider(bot, args: str):
    """LLM-Provider anzeigen oder wechseln"""
    from ce365.core.providers import create_provider, DEFAULT_MODELS
    from ce365.config.settings import get_settings

    settings = get_settings()
    provider_keys = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "openrouter": settings.openrouter_api_key,
    }

    target = args.strip().lower() if args.strip() else None

    if not target:
        # Status anzeigen
        bot.console.display_separator()
        bot.console.console.print("[bold]LLM-Provider Status:[/bold]\n")
        for name, key in provider_keys.items():
            status = "[green]Key vorhanden[/green]" if key else "[red]Kein Key[/red]"
            active = " [bold cyan]<< aktiv[/bold cyan]" if name == settings.llm_provider else ""
            bot.console.console.print(f"  {name:<14} {status}{active}")
        bot.console.console.print(f"\n  Modell: {settings.llm_model}")
        bot.console.console.print(f"\n  Wechseln: /provider <name>")
        bot.console.console.print()
        return

    # Provider wechseln
    if target not in provider_keys:
        bot.console.display_error(
            f"Unbekannter Provider: {target}\n"
            f"Verfuegbar: {', '.join(provider_keys.keys())}"
        )
        return

    if not provider_keys[target]:
        bot.console.display_error(
            f"Kein API-Key fuer '{target}' konfiguriert.\n"
            f"Setze den Key in der .env Datei."
        )
        return

    if target == settings.llm_provider:
        bot.console.display_info(f"'{target}' ist bereits der aktive Provider.")
        return

    # Hot-Swap
    new_model = DEFAULT_MODELS.get(target, "")
    try:
        new_client = create_provider(
            provider_name=target,
            api_key=provider_keys[target],
            model=new_model,
        )
        bot.client = new_client
        settings.llm_provider = target
        settings.llm_model = new_model
        settings.save()
        bot.console.display_success(
            f"Provider gewechselt: {target} (Modell: {new_model})"
        )
    except Exception as e:
        bot.console.display_error(f"Provider-Wechsel fehlgeschlagen: {e}")


async def _cmd_model(bot, args: str):
    """LLM-Modell anzeigen oder wechseln"""
    from ce365.core.providers import create_provider, DEFAULT_MODELS
    from ce365.config.settings import get_settings

    settings = get_settings()
    target = args.strip() if args.strip() else None

    if not target:
        # Status anzeigen
        bot.console.display_separator()
        bot.console.console.print("[bold]LLM-Modell Status:[/bold]\n")
        bot.console.console.print(f"  Provider: {settings.llm_provider}")
        bot.console.console.print(f"  Modell:   {settings.llm_model}")
        bot.console.console.print()
        bot.console.console.print("[bold]Verfuegbare Modelle:[/bold]")
        try:
            available = bot.client.list_models()
            for model in available[:3]:
                active = " [bold cyan]<< aktiv[/bold cyan]" if model == settings.llm_model else ""
                bot.console.console.print(f"  {model}{active}")
        except Exception:
            bot.console.display_warning("Modell-Liste konnte nicht abgerufen werden.")
        bot.console.console.print(f"\n  Wechseln: /model <name>")
        bot.console.console.print()
        return

    if target == settings.llm_model:
        bot.console.display_info(f"'{target}' ist bereits das aktive Modell.")
        return

    # Hot-Swap: neuen Provider mit neuem Modell erstellen
    provider_keys = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    try:
        new_client = create_provider(
            provider_name=settings.llm_provider,
            api_key=provider_keys[settings.llm_provider],
            model=target,
        )
        bot.client = new_client
        settings.llm_model = target
        settings.save()
        bot.console.display_success(
            f"Modell gewechselt: {target} (Provider: {settings.llm_provider})"
        )
    except Exception as e:
        bot.console.display_error(f"Modell-Wechsel fehlgeschlagen: {e}")


async def _cmd_stats(bot, args: str):
    """Learning-Statistiken anzeigen"""
    try:
        stats = bot.case_library.get_statistics()
        bot.console.display_learning_stats(stats)
    except Exception as e:
        bot.console.display_error(f"Stats-Fehler: {e}")


async def _cmd_privacy(bot, args: str):
    """Datenschutz-Menue aufrufen"""
    await bot._handle_privacy_command()


async def _cmd_config(bot, args: str):
    """Einstellungen anzeigen und aendern — interaktives Menue"""
    from ce365.config.settings import get_settings
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from pathlib import Path
    import os

    settings = get_settings()
    console = bot.console.console

    # .env Datei finden
    if getattr(sys, "frozen", False):
        env_path = Path(sys.executable).parent / ".env"
    else:
        env_path = Path(".env")

    def _update_env(key: str, value: str):
        """Aktualisiert einen Wert in der .env Datei"""
        if not env_path.exists():
            return
        content = env_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")
        env_path.write_text("\n".join(lines), encoding="utf-8")

    # Direktaufruf mit Argument (z.B. /config apikey)
    target = args.strip().lower() if args.strip() else None

    if not target:
        # ── Interaktives Menue ──
        bot.console.display_separator()

        # Aktuelle Einstellungen
        table = Table(show_header=False, border_style="dim", padding=(0, 2))
        table.add_column("Key", style="cyan", min_width=14)
        table.add_column("Value")

        table.add_row("Edition", settings.edition.title())
        table.add_row("Provider", settings.llm_provider)
        table.add_row("Modell", settings.llm_model or "(Provider-Default)")
        table.add_row("Passwort", "[green]Gesetzt[/green]" if settings.technician_password_hash else "[red]Nicht gesetzt[/red]")
        table.add_row("Datenbank", settings.learning_db_type)
        if settings.learning_db_url:
            db_display = settings.learning_db_url.split("@")[-1] if "@" in settings.learning_db_url else settings.learning_db_url
            table.add_row("DB-Server", db_display)
        table.add_row("Lizenz", "***" + settings.license_key[-8:] if settings.license_key else "Keiner")

        console.print(Panel(table, title="[bold]Aktuelle Einstellungen[/bold]", border_style="cyan", padding=(1, 2)))
        console.print()

        # Menue-Optionen
        console.print("[bold]Was moechtest du aendern?[/bold]\n")
        console.print("  [cyan]1[/cyan]  API-Key aendern")
        console.print("  [cyan]2[/cyan]  LLM-Provider wechseln")
        console.print("  [cyan]3[/cyan]  Datenbank konfigurieren")
        console.print("  [cyan]4[/cyan]  Passwort aendern")
        console.print("  [cyan]5[/cyan]  Briefing aendern")
        console.print("  [cyan]6[/cyan]  Lizenzschluessel aendern")
        console.print("  [cyan]7[/cyan]  Kompletten Setup-Wizard neu starten")
        console.print("  [cyan]0[/cyan]  Zurueck\n")

        choice = Prompt.ask("  Wahl", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="0")

        target_map = {
            "1": "apikey",
            "2": "provider",
            "3": "db",
            "4": "password",
            "5": "briefing",
            "6": "license",
            "7": "wizard",
            "0": None,
        }
        target = target_map.get(choice)

        if not target:
            bot.console.display_info("Zurueck zum Chat.")
            return

    if not env_path.exists():
        bot.console.display_error(f".env nicht gefunden: {env_path}")
        return

    # ── Einzelne Einstellungen aendern ──

    if target == "apikey":
        console.print("\n[bold]API-Key aendern[/bold]")
        console.print(f"  Aktueller Provider: [cyan]{settings.llm_provider}[/cyan]\n")
        new_key = Prompt.ask("  Neuer API-Key", password=True)
        if not new_key:
            bot.console.display_info("Abgebrochen.")
            return
        key_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        env_var = key_env_map.get(settings.llm_provider, "ANTHROPIC_API_KEY")
        _update_env(env_var, new_key)
        os.environ[env_var] = new_key
        bot.console.display_success(f"API-Key fuer {settings.llm_provider} aktualisiert. Neustart empfohlen.")

    elif target == "provider":
        from ce365.core.providers import create_provider, DEFAULT_MODELS
        console.print("\n[bold]LLM-Provider wechseln[/bold]")
        console.print(f"  Aktuell: [cyan]{settings.llm_provider}[/cyan]\n")
        console.print("  [cyan]1[/cyan]  Anthropic (Claude)")
        console.print("  [cyan]2[/cyan]  OpenAI (GPT)")
        console.print("  [cyan]3[/cyan]  OpenRouter (viele Modelle)\n")
        choice = Prompt.ask("  Wahl", choices=["1", "2", "3"], default="1")
        provider_map = {"1": "anthropic", "2": "openai", "3": "openrouter"}
        new_provider = provider_map[choice]

        if new_provider == settings.llm_provider:
            bot.console.display_info(f"'{new_provider}' ist bereits aktiv.")
            return

        # API-Key fuer neuen Provider pruefen
        key_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        provider_keys = {
            "anthropic": settings.anthropic_api_key,
            "openai": settings.openai_api_key,
            "openrouter": settings.openrouter_api_key,
        }
        if not provider_keys.get(new_provider):
            console.print(f"\n  Kein API-Key fuer {new_provider} vorhanden.")
            new_key = Prompt.ask(f"  {new_provider.title()} API-Key", password=True)
            if not new_key:
                bot.console.display_info("Abgebrochen.")
                return
            _update_env(key_env_map[new_provider], new_key)
            os.environ[key_env_map[new_provider]] = new_key
            provider_keys[new_provider] = new_key

        # Provider + Model wechseln
        new_model = DEFAULT_MODELS.get(new_provider)
        try:
            new_client = create_provider(
                provider_name=new_provider,
                api_key=provider_keys[new_provider],
                model=new_model,
            )
            bot.client = new_client
            settings.llm_provider = new_provider
            settings.llm_model = new_model
            _update_env("LLM_PROVIDER", new_provider)
            settings.save()
            bot.console.display_success(f"Provider gewechselt: {new_provider} (Modell: {new_model})")
        except Exception as e:
            bot.console.display_error(f"Provider-Wechsel fehlgeschlagen: {e}")

    elif target == "password":
        import bcrypt
        console.print("\n[bold]Passwort aendern[/bold]\n")
        new_pw = Prompt.ask("  Neues Passwort", password=True)
        if not new_pw or len(new_pw) < 6:
            bot.console.display_error("Passwort zu kurz (min. 6 Zeichen).")
            return
        confirm_pw = Prompt.ask("  Wiederholen", password=True)
        if new_pw != confirm_pw:
            bot.console.display_error("Passwoerter stimmen nicht ueberein.")
            return
        pw_hash = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        _update_env("TECHNICIAN_PASSWORD_HASH", pw_hash)
        bot.console.display_success("Passwort aktualisiert.")

    elif target == "db":
        console.print("\n[bold]Datenbank konfigurieren[/bold]")
        console.print(f"  Aktuell: [cyan]{settings.learning_db_type}[/cyan]\n")
        console.print("  [cyan]1[/cyan]  SQLite (lokal)")
        console.print("  [cyan]2[/cyan]  MySQL/MariaDB")
        console.print("  [cyan]3[/cyan]  PostgreSQL\n")
        choice = Prompt.ask("  Wahl", choices=["1", "2", "3"], default="1")
        if choice == "1":
            _update_env("LEARNING_DB_TYPE", "sqlite")
            _update_env("LEARNING_DB_URL", "")
            bot.console.display_success("Datenbank auf SQLite umgestellt. Neustart erforderlich.")
        else:
            db_type = "mysql" if choice == "2" else "postgresql"
            host = Prompt.ask("  Host", default="localhost")
            port = Prompt.ask("  Port", default="3306" if db_type == "mysql" else "5432")
            database = Prompt.ask("  Database", default="ce365_learning")
            user = Prompt.ask("  Username", default="ce365")
            password = Prompt.ask("  Password", password=True)
            driver = "asyncmy" if db_type == "mysql" else "asyncpg"
            db_url = f"{db_type}+{driver}://{user}:{password}@{host}:{port}/{database}"
            _update_env("LEARNING_DB_TYPE", db_type)
            _update_env("LEARNING_DB_URL", db_url)
            bot.console.display_success(f"Datenbank auf {db_type.upper()} umgestellt. Neustart erforderlich.")

    elif target == "briefing":
        console.print("\n[bold]Briefing aendern[/bold]\n")
        new_briefing = Prompt.ask("  Neues Briefing", default="")
        _update_env("BRIEFING", new_briefing)
        bot.console.display_success("Briefing aktualisiert.")

    elif target == "license":
        console.print("\n[bold]Lizenzschluessel aendern[/bold]\n")
        new_key = Prompt.ask("  Neuer Lizenzschluessel", password=True)
        if not new_key:
            bot.console.display_info("Abgebrochen.")
            return
        _update_env("LICENSE_KEY", new_key)
        bot.console.display_success("Lizenzschluessel aktualisiert. Neustart erforderlich.")

    elif target == "wizard":
        console.print("\n[yellow]Setup-Wizard neu starten[/yellow]")
        console.print("[dim]Alle Einstellungen werden neu konfiguriert. CE365 wird danach beendet.[/dim]\n")
        if Confirm.ask("  Fortfahren?", default=False):
            from ce365.setup.wizard import SetupWizard
            wizard = SetupWizard()
            wizard.run()
            console.print("\n[yellow]Bitte CE365 neu starten.[/yellow]")
            sys.exit(0)
        else:
            bot.console.display_info("Abgebrochen.")

    else:
        bot.console.display_error(
            f"Unbekannte Option: {target}\n"
            "Verfuegbar: apikey, provider, db, password, briefing, license, wizard"
        )


async def _cmd_scan(bot, args: str):
    """Vollstaendige System-Analyse durchfuehren"""
    await bot.run_full_scan()


async def _cmd_update(bot, args: str):
    """CE365 auf neueste Version aktualisieren"""
    from ce365.core.updater import run_update
    run_update()


async def _cmd_rollback(bot, args: str):
    """Rollback zur vorherigen Version"""
    from ce365.core.updater import run_rollback
    run_rollback()


async def _cmd_check(bot, args: str):
    """Audit-Routine ausfuehren — mit Profil-Auswahl"""
    from rich.prompt import Prompt
    from ce365.core.routines import run_routine, get_routine_names, get_routine_menu

    target = args.strip().lower() if args.strip() else None

    if not target:
        # Interaktives Auswahl-Menu
        console = bot.console.console
        bot.console.display_separator()
        console.print("[bold]Audit-Routinen[/bold]\n")

        menu = get_routine_menu()
        for i, (name, label, desc) in enumerate(menu, 1):
            console.print(f"  [cyan]{i}[/cyan]  {label}  [dim]— {desc}[/dim]")
        console.print(f"  [cyan]0[/cyan]  Zurueck\n")

        choices = [str(i) for i in range(len(menu) + 1)]
        choice = Prompt.ask("  Wahl", choices=choices, default="0")
        idx = int(choice)
        if idx == 0:
            bot.console.display_info("Zurueck zum Chat.")
            return
        target = menu[idx - 1][0]

    if target not in get_routine_names():
        bot.console.display_error(
            f"Unbekannte Routine: {target}\n"
            f"Verfuegbar: {', '.join(get_routine_names())}"
        )
        return

    await run_routine(bot, target)
