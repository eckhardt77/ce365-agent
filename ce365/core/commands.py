"""
CE365 Agent - Slash Command System

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Dispatcher fuer /command Eingaben im Main-Loop.
"""

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
    report_tool = bot.tool_registry.get_tool("generate_incident_report")
    if not report_tool:
        bot.console.display_error("Incident Report Tool nicht verfuegbar.")
        return

    fmt = args.strip().lower() if args.strip() else None

    if not fmt:
        choice = bot.console.get_input(
            "Report-Format? [M]arkdown / [S]OAP"
        ).strip().lower()
        if choice in ("m", "markdown"):
            fmt = "markdown"
        elif choice in ("s", "soap"):
            fmt = "soap"
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
                f"Unbekanntes Format: {fmt}. Verfuegbar: markdown, soap"
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
