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

        # Bare "/" zeigt interaktives Menue (gruppiert wie Claude Code)
        if not raw_cmd:
            from rich.prompt import Prompt
            console = bot.console.console
            bot.console.display_separator()
            console.print("[bold]Befehle[/bold]\n")

            # Gruppierte Befehlsliste
            groups = [
                ("Diagnose & Analyse", ["scan", "check", "report", "stats"]),
                ("Remote & Integration", ["connect", "disconnect", "remote", "mcp"]),
                ("Einstellungen", ["provider", "model", "config", "privacy"]),
                ("System", ["update", "rollback", "help"]),
            ]

            flat_cmds = []
            idx = 1
            for group_name, cmd_names in groups:
                group_items = []
                for cn in cmd_names:
                    cmd_obj = self._commands.get(cn)
                    if cmd_obj:
                        group_items.append((idx, cmd_obj))
                        flat_cmds.append(cmd_obj)
                        idx += 1
                if group_items:
                    console.print(f"  [bold dim]{group_name}[/bold dim]")
                    for num, cmd_obj in group_items:
                        alias_hint = ""
                        if cmd_obj.aliases:
                            main_aliases = [a for a in cmd_obj.aliases if a.startswith("/") or len(a) <= 3]
                            if main_aliases:
                                alias_hint = f" [dim](/{main_aliases[0]})[/dim]"
                        console.print(f"    [cyan]{num:>2}[/cyan]  /{cmd_obj.name:<14} {cmd_obj.description}{alias_hint}")
                    console.print()

            console.print(f"   [cyan]0[/cyan]  Zurueck\n")
            choices = [str(i) for i in range(len(flat_cmds) + 1)]
            choice = Prompt.ask("  Wahl", choices=choices, default="0")
            idx = int(choice)
            if idx == 0:
                bot.console.display_info("Zurueck zum Chat.")
                return True
            selected = flat_cmds[idx - 1]
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
        self.register(SlashCommand(
            name="mcp",
            aliases=[],
            description="MCP-Server verwalten (list/connect/disconnect/tools)",
            handler=_cmd_mcp,
        ))
        self.register(SlashCommand(
            name="connect",
            aliases=["ssh"],
            description="SSH-Verbindung zu Remote-Host herstellen",
            handler=_cmd_connect,
        ))
        self.register(SlashCommand(
            name="disconnect",
            aliases=[],
            description="SSH-Verbindung trennen",
            handler=_cmd_disconnect,
        ))
        self.register(SlashCommand(
            name="remote",
            aliases=[],
            description="Remote-Verbindungsstatus anzeigen",
            handler=_cmd_remote,
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
    """PDF-Report auf Desktop generieren — sammelt alle Audit-Tool-Ergebnisse"""
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

    # Alle relevanten Audit-Tools ausfuehren
    tools_to_run = [
        ("check_security_status", "Sicherheitsstatus"),
        ("check_backup_status", "Backup-Status"),
        ("check_disk_health", "Festplatten-Gesundheit"),
        ("check_network_security", "Netzwerk-Sicherheit"),
        ("check_system_updates", "System-Updates"),
        ("check_running_processes", "Laufende Prozesse"),
        ("check_battery_health", "Akku-Status"),
    ]

    sections = []
    for tool_name, section_title in tools_to_run:
        tool = bot.tool_registry.get_tool(tool_name)
        if not tool:
            continue
        try:
            with bot.console.show_spinner(f"Pruefe {section_title}"):
                result = await tool.execute()
            if result and isinstance(result, str) and len(result.strip()) > 10:
                sections.append({"title": section_title, "content": result})
        except Exception:
            pass

    report_data = {
        "system_info": system_info,
        "sections": sections,
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
    """LLM-Modell anzeigen oder wechseln — interaktive Auswahl"""
    from ce365.core.providers import create_provider, DEFAULT_MODELS, RECOMMENDED_MODELS
    from ce365.config.settings import get_settings
    from rich.prompt import Prompt

    settings = get_settings()
    target = args.strip() if args.strip() else None

    if not target:
        # Interaktive Modell-Auswahl
        console = bot.console.console
        bot.console.display_separator()
        console.print("[bold]LLM-Modell[/bold]\n")
        console.print(f"  Provider: [cyan]{settings.llm_provider}[/cyan]")
        console.print(f"  Modell:   [cyan]{settings.llm_model}[/cyan]\n")

        # Kuratierte Modelle fuer den aktiven Provider
        recommended = RECOMMENDED_MODELS.get(settings.llm_provider, [])
        if recommended:
            console.print("[bold]Empfohlene Modelle:[/bold]\n")
            for i, (model_id, desc) in enumerate(recommended, 1):
                active = " [bold cyan]<< aktiv[/bold cyan]" if model_id == settings.llm_model else ""
                console.print(f"  [cyan]{i}[/cyan]  {model_id:<28} [dim]{desc}[/dim]{active}")
            console.print(f"  [cyan]0[/cyan]  Zurueck\n")

            # Auch freie Eingabe ermoeglichen
            choices = [str(i) for i in range(len(recommended) + 1)]
            choice = Prompt.ask("  Wahl (oder Modell-Name eingeben)", default="0")

            if choice in choices:
                idx = int(choice)
                if idx == 0:
                    bot.console.display_info("Zurueck zum Chat.")
                    return
                target = recommended[idx - 1][0]
            else:
                target = choice.strip()
        else:
            # Fallback: API-Liste
            try:
                available = bot.client.list_models()
                for model in available[:5]:
                    active = " [bold cyan]<< aktiv[/bold cyan]" if model == settings.llm_model else ""
                    console.print(f"  {model}{active}")
            except Exception:
                bot.console.display_warning("Modell-Liste konnte nicht abgerufen werden.")
            console.print(f"\n  Wechseln: /model <name>")
            console.print()
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
        env_path = Path(sys.executable).parent / "config" / ".env"
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


# ==========================================
# SSH REMOTE COMMANDS
# ==========================================

async def _cmd_connect(bot, args: str):
    """Remote-Verbindung herstellen (SSH oder WinRM)

    SSH:   /connect <host> [--user root] [--key ~/.ssh/id_rsa] [--port 22]
    WinRM: /connect <host> --winrm [--user Administrator] [--password ...] [--port 5985] [--ssl]
    """
    from ce365.core.license import check_edition_features
    from ce365.config.settings import get_settings

    settings = get_settings()
    if not check_edition_features(settings.edition, "ssh_remote"):
        bot.console.display_error("Remote-Zugriff ist ein Pro-Feature.")
        return

    if not args.strip():
        bot.console.display_error(
            "Verwendung:\n"
            "  SSH:   /connect <host> [--user root] [--key ~/.ssh/id_rsa] [--port 22]\n"
            "  WinRM: /connect <host> --winrm [--user Administrator] [--password ...] [--ssl]"
        )
        return

    # Argumente parsen
    parts = args.strip().split()
    host = parts[0]
    username = None  # Default wird spaeter je nach Transport gesetzt
    key_path = None
    password = None
    port = None
    use_winrm = False
    use_ssl = False

    i = 1
    while i < len(parts):
        flag = parts[i].lower()
        if flag == "--user" and i + 1 < len(parts):
            username = parts[i + 1]
            i += 2
        elif flag == "--key" and i + 1 < len(parts):
            key_path = parts[i + 1]
            i += 2
        elif flag == "--password" and i + 1 < len(parts):
            password = parts[i + 1]
            i += 2
        elif flag == "--port" and i + 1 < len(parts):
            try:
                port = int(parts[i + 1])
            except ValueError:
                bot.console.display_error(f"Ungueltiger Port: {parts[i + 1]}")
                return
            i += 2
        elif flag == "--winrm":
            use_winrm = True
            i += 1
        elif flag == "--ssl":
            use_ssl = True
            i += 1
        else:
            i += 1

    from ce365.core.command_runner import get_command_runner
    runner = get_command_runner()

    if use_winrm:
        # === WinRM-Verbindung ===
        if not hasattr(bot, "winrm_manager") or bot.winrm_manager is None:
            bot.console.display_error("WinRM-Manager nicht initialisiert.")
            return

        winrm_user = username or "Administrator"
        winrm_port = port or (5986 if use_ssl else 5985)

        # Passwort abfragen wenn nicht angegeben
        if not password:
            from rich.prompt import Prompt
            password = Prompt.ask(
                f"  Passwort fuer {winrm_user}@{host}",
                password=True,
            )
            if not password:
                bot.console.display_info("Abgebrochen.")
                return

        try:
            proto = "HTTPS" if use_ssl else "HTTP"
            bot.console.display_info(
                f"Verbinde mit {winrm_user}@{host}:{winrm_port} (WinRM/{proto})..."
            )
            conn = await bot.winrm_manager.connect(
                host=host,
                port=winrm_port,
                username=winrm_user,
                password=password,
                ssl=use_ssl,
                verify_ssl=False,  # Selbstsignierte Zertifikate erlauben
            )

            runner.set_winrm(conn)

            bot.console.display_success(f"Verbunden mit {conn.host_display}")
            bot.console.display_info(
                "Alle Tools laufen jetzt auf dem Remote-Windows-System. "
                "Trenne mit /disconnect."
            )

        except Exception as e:
            bot.console.display_error(f"WinRM-Verbindung fehlgeschlagen: {e}")

    else:
        # === SSH-Verbindung ===
        if not hasattr(bot, "ssh_manager") or bot.ssh_manager is None:
            bot.console.display_error("SSH-Manager nicht initialisiert.")
            return

        ssh_user = username or "root"
        ssh_port = port or 22

        try:
            bot.console.display_info(f"Verbinde mit {ssh_user}@{host}:{ssh_port} (SSH)...")
            conn = await bot.ssh_manager.connect(
                host=host,
                port=ssh_port,
                username=ssh_user,
                key_path=key_path,
                password=password,
            )

            runner.set_remote(conn)

            bot.console.display_success(f"Verbunden mit {conn.host_display}")
            bot.console.display_info(
                "Alle Tools laufen jetzt auf dem Remote-System. "
                "Trenne mit /disconnect."
            )

        except Exception as e:
            bot.console.display_error(f"SSH-Verbindung fehlgeschlagen: {e}")


async def _cmd_disconnect(bot, args: str):
    """Remote-Verbindung trennen (SSH oder WinRM)"""
    from ce365.core.command_runner import get_command_runner
    runner = get_command_runner()

    if runner.mode == "winrm":
        # WinRM trennen
        if hasattr(bot, "winrm_manager") and bot.winrm_manager and bot.winrm_manager.is_connected:
            host = bot.winrm_manager.host_display
            await bot.winrm_manager.disconnect()
            runner.set_local()
            bot.console.display_success(f"WinRM-Verbindung zu {host} getrennt.")
            bot.console.display_info("Alle Tools laufen jetzt wieder lokal.")
        else:
            bot.console.display_info("Keine aktive WinRM-Verbindung.")

    elif runner.mode == "remote":
        # SSH trennen
        if hasattr(bot, "ssh_manager") and bot.ssh_manager and bot.ssh_manager.is_connected:
            host = bot.ssh_manager.host_display
            await bot.ssh_manager.disconnect()
            runner.set_local()
            bot.console.display_success(f"SSH-Verbindung zu {host} getrennt.")
            bot.console.display_info("Alle Tools laufen jetzt wieder lokal.")
        else:
            bot.console.display_info("Keine aktive SSH-Verbindung.")

    else:
        bot.console.display_info("Keine aktive Remote-Verbindung.")


async def _cmd_remote(bot, args: str):
    """Remote-Verbindungsstatus anzeigen"""
    from ce365.core.command_runner import get_command_runner
    runner = get_command_runner()

    bot.console.display_separator()
    bot.console.console.print("[bold]Remote-Verbindung:[/bold]\n")

    if runner.is_remote:
        transport = runner.transport.upper()
        bot.console.console.print(f"  Status:    [green]Verbunden[/green]")
        bot.console.console.print(f"  Transport: {transport}")
        bot.console.console.print(f"  Host:      {runner.remote_host}")

        if runner.mode == "remote" and hasattr(bot, "ssh_manager") and bot.ssh_manager:
            status = bot.ssh_manager.get_status()
            bot.console.console.print(f"  Port:      {status.get('port', '?')}")
            bot.console.console.print(f"  User:      {status.get('username', '?')}")

        elif runner.mode == "winrm" and hasattr(bot, "winrm_manager") and bot.winrm_manager:
            status = bot.winrm_manager.get_status()
            bot.console.console.print(f"  Port:      {status.get('port', '?')}")
            bot.console.console.print(f"  User:      {status.get('username', '?')}")
            bot.console.console.print(f"  SSL:       {'Ja' if status.get('ssl') else 'Nein'}")

        bot.console.console.print(f"\n  Trennen: /disconnect")

    else:
        bot.console.console.print("  Status:    [red]Nicht verbunden[/red]")
        bot.console.console.print("")
        bot.console.console.print("  SSH:   /connect <host> [--user root]")
        bot.console.console.print("  WinRM: /connect <host> --winrm [--user Administrator]")

    bot.console.console.print()


# ==========================================
# MCP SERVER COMMANDS
# ==========================================

async def _cmd_mcp(bot, args: str):
    """MCP-Server verwalten: /mcp list|connect|disconnect|tools <name>"""
    from ce365.core.license import check_edition_features
    from ce365.config.settings import get_settings

    settings = get_settings()
    if not check_edition_features(settings.edition, "mcp_integration"):
        bot.console.display_error("MCP-Integration ist ein Pro-Feature.")
        return

    if not hasattr(bot, "mcp_manager") or bot.mcp_manager is None:
        bot.console.display_error("MCP-Manager nicht initialisiert.")
        return

    parts = args.strip().split(maxsplit=1) if args.strip() else []
    action = parts[0].lower() if parts else "list"
    target = parts[1].strip() if len(parts) > 1 else ""

    if action == "list":
        # Alle Server und Status anzeigen
        status_list = bot.mcp_manager.get_server_status()
        bot.console.display_separator()
        bot.console.console.print("[bold]MCP-Server:[/bold]\n")

        if not status_list:
            bot.console.console.print("  Keine MCP-Server konfiguriert.")
            bot.console.console.print(f"  Konfiguration: {bot.mcp_manager.config_path}")
        else:
            for s in status_list:
                status_icon = "[green]Verbunden[/green]" if s["connected"] else "[red]Getrennt[/red]"
                tools_info = f" ({s['tool_count']} Tools)" if s["connected"] else ""
                bot.console.console.print(
                    f"  {s['name']:<16} {status_icon}{tools_info}"
                )
                bot.console.console.print(f"  {'':16} {s['url']}")
        bot.console.console.print()

    elif action == "connect":
        if not target:
            names = bot.mcp_manager.get_server_names()
            bot.console.display_error(
                f"Verwendung: /mcp connect <name>\n"
                f"Verfuegbar: {', '.join(names) or 'keine'}"
            )
            return

        try:
            bot.console.display_info(f"Verbinde mit MCP-Server '{target}'...")
            proxy_tools = await bot.mcp_manager.connect(target)

            # Proxy-Tools in Registry registrieren
            registered = 0
            for tool in proxy_tools:
                try:
                    bot.tool_registry.register(tool)
                    registered += 1
                except ValueError:
                    pass  # Tool-Name bereits registriert

            bot.console.display_success(
                f"MCP-Server '{target}' verbunden — {registered} Tools registriert"
            )

            # Tool-Namen anzeigen
            if proxy_tools:
                tool_names = [t.name for t in proxy_tools]
                bot.console.console.print(
                    f"  Tools: {', '.join(tool_names[:10])}"
                    + (f" (+{len(tool_names) - 10} weitere)" if len(tool_names) > 10 else "")
                )

        except Exception as e:
            bot.console.display_error(f"MCP-Verbindung fehlgeschlagen: {e}")

    elif action == "disconnect":
        if not target:
            bot.console.display_error("Verwendung: /mcp disconnect <name>")
            return

        try:
            tool_names = await bot.mcp_manager.disconnect(target)

            # Proxy-Tools aus Registry entfernen
            for tool_name in tool_names:
                bot.tool_registry.unregister(tool_name)

            bot.console.display_success(
                f"MCP-Server '{target}' getrennt — {len(tool_names)} Tools entfernt"
            )

        except Exception as e:
            bot.console.display_error(f"MCP-Trennung fehlgeschlagen: {e}")

    elif action == "tools":
        if not target:
            bot.console.display_error("Verwendung: /mcp tools <name>")
            return

        tools = bot.mcp_manager.get_tools_for_server(target)
        if not tools:
            bot.console.display_info(f"Keine Tools fuer '{target}' (nicht verbunden?)")
            return

        bot.console.display_separator()
        bot.console.console.print(f"[bold]MCP-Tools ({target}):[/bold]\n")
        for tool in tools:
            bot.console.console.print(f"  {tool.name:<30} {tool.description[:60]}")
        bot.console.console.print()

    else:
        bot.console.display_error(
            f"Unbekannte MCP-Aktion: {action}\n"
            "Verfuegbar: list, connect, disconnect, tools"
        )
