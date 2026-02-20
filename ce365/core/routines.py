"""
CE365 Agent - Audit-Routinen System

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Vordefinierte Pruefablaeufe die mehrere Tools automatisch
hintereinander ausfuehren und Ergebnisse an Claude uebergeben.
"""

from typing import Dict, List, Tuple

# ============================================================
# ROUTINEN-PROFILE
# ============================================================

ROUTINES: Dict[str, dict] = {
    "komplett": {
        "label": "Komplett-Check",
        "icon": "🔍",
        "description": "Alle wichtigen Audit-Tools durchlaufen",
        "tools": [
            ("System-Informationen", "get_system_info", {}),
            ("Laufende Prozesse", "check_running_processes", {"sort_by": "cpu", "limit": 10}),
            ("System-Logs", "check_system_logs", {}),
            ("Sicherheits-Status", "check_security_status", {}),
            ("Updates", "check_system_updates", {}),
            ("Autostart-Programme", "check_startup_programs", {}),
            ("Backup-Status", "check_backup_status", {}),
            ("Festplatten-Gesundheit", "check_disk_health", {}),
            ("Netzwerk-Sicherheit", "check_network_security", {}),
            ("Benutzerkonten", "audit_user_accounts", {}),
        ],
        "prompt": (
            "Du hast gerade einen vollstaendigen System-Check durchgefuehrt. "
            "Hier sind die Ergebnisse aller Audit-Tools:\n\n"
            "{scan_data}\n\n"
            "---\n\n"
            "Bitte analysiere die Ergebnisse und erstelle eine priorisierte Uebersicht:\n"
            "1. Nummeriere alle Findings\n"
            "2. Verwende 🔴 fuer kritische Probleme (sofort handeln)\n"
            "3. Verwende 🟡 fuer Warnungen (sollte behoben werden)\n"
            "4. Verwende 🟢 fuer OK-Bereiche (kurz zusammenfassen)\n\n"
            "Am Ende frage: 'Welche Punkte soll ich beheben? (z.B. \"1,3\")'\n"
            "Falls alles OK ist, sage das und biete an einen Report zu erstellen.\n"
            "Frage am Ende auch: 'Report als PDF auf den Desktop speichern? [J/N]'"
        ),
    },
    "sicherheit": {
        "label": "Sicherheits-Check",
        "icon": "🛡️",
        "description": "Security-fokussierte Pruefung",
        "tools": [
            ("Malware-Scan", "scan_malware", {}),
            ("Sicherheits-Status", "check_security_status", {}),
            ("Verschluesselung", "check_encryption_status", {}),
            ("Netzwerk-Sicherheit", "check_network_security", {}),
            ("Benutzerkonten", "audit_user_accounts", {}),
            ("Hosts-Datei", "check_hosts_file", {}),
        ],
        "prompt": (
            "Du hast gerade einen Sicherheits-Check durchgefuehrt. "
            "Hier sind die Ergebnisse:\n\n"
            "{scan_data}\n\n"
            "---\n\n"
            "Analysiere die Ergebnisse mit Fokus auf Sicherheit:\n"
            "1. Nummeriere alle Findings\n"
            "2. 🔴 Akute Bedrohungen oder Schwachstellen\n"
            "3. 🟡 Sicherheitsempfehlungen und Haertungsmassnahmen\n"
            "4. 🟢 Bereits gut abgesicherte Bereiche\n\n"
            "Priorisiere nach Risiko. Bei Findings: "
            "'Welche Punkte soll ich beheben? (z.B. \"1,3\")'\n"
            "Frage am Ende: 'Sicherheits-Report als PDF speichern? [J/N]'"
        ),
    },
    "performance": {
        "label": "Performance-Check",
        "icon": "⚡",
        "description": "Performance und Ressourcen pruefen",
        "tools": [
            ("System-Informationen", "get_system_info", {}),
            ("Laufende Prozesse", "check_running_processes", {"sort_by": "cpu", "limit": 15}),
            ("Festplatten-Gesundheit", "check_disk_health", {}),
            ("Autostart-Programme", "check_startup_programs", {}),
            ("System-Temperaturen", "check_system_temperature", {}),
        ],
        "prompt": (
            "Du hast gerade einen Performance-Check durchgefuehrt. "
            "Hier sind die Ergebnisse:\n\n"
            "{scan_data}\n\n"
            "---\n\n"
            "Analysiere die Ergebnisse mit Fokus auf Performance:\n"
            "1. Nummeriere alle Findings\n"
            "2. 🔴 Kritische Engpaesse (hohe CPU/RAM-Auslastung, volle Festplatte)\n"
            "3. 🟡 Optimierungspotenzial (unnoetige Autostart-Programme, langsame Disk)\n"
            "4. 🟢 Gut performende Bereiche\n\n"
            "Gib konkrete Empfehlungen zur Optimierung. "
            "'Welche Punkte soll ich optimieren? (z.B. \"1,3\")'\n"
            "Frage am Ende: 'Performance-Report als PDF speichern? [J/N]'"
        ),
    },
    "wartung": {
        "label": "Wartungs-Check",
        "icon": "🔧",
        "description": "Wartungsstatus und Updates pruefen",
        "tools": [
            ("System-Updates", "check_system_updates", {}),
            ("Backup-Status", "check_backup_status", {}),
            ("Treiber-Status", "check_drivers", {}),
            ("Festplatten-Gesundheit", "check_disk_health", {}),
            ("Geplante Aufgaben", "audit_scheduled_tasks", {}),
        ],
        "prompt": (
            "Du hast gerade einen Wartungs-Check durchgefuehrt. "
            "Hier sind die Ergebnisse:\n\n"
            "{scan_data}\n\n"
            "---\n\n"
            "Analysiere die Ergebnisse mit Fokus auf Wartung:\n"
            "1. Nummeriere alle Findings\n"
            "2. 🔴 Ueberfaellige Updates, fehlende Backups, defekte Treiber\n"
            "3. 🟡 Empfohlene Wartungsarbeiten\n"
            "4. 🟢 Aktuelle und gepflegte Bereiche\n\n"
            "Priorisiere nach Dringlichkeit. "
            "'Welche Punkte soll ich beheben? (z.B. \"1,3\")'\n"
            "Frage am Ende: 'Wartungs-Report als PDF speichern? [J/N]'"
        ),
    },
}


def get_routine_names() -> List[str]:
    """Alle verfuegbaren Routinen-Namen"""
    return list(ROUTINES.keys())


def get_routine_menu() -> List[Tuple[str, str, str]]:
    """Menu-Eintraege: (name, icon + label, description)"""
    return [
        (name, f"{r['icon']} {r['label']}", r["description"])
        for name, r in ROUTINES.items()
    ]


# ============================================================
# ROUTINE RUNNER
# ============================================================

async def run_routine(bot, routine_name: str):
    """
    Routine ausfuehren: Tools sequentiell starten, Fortschritt
    anzeigen, Ergebnisse sammeln und an Claude uebergeben.

    Args:
        bot: Bot-Instanz (fuer tool_registry, console, process_message)
        routine_name: Key aus ROUTINES dict
    """
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    from rich import box
    from ce365.ui.console import _get_width

    routine = ROUTINES.get(routine_name)
    if not routine:
        bot.console.display_error(
            f"Unbekannte Routine: {routine_name}\n"
            f"Verfuegbar: {', '.join(get_routine_names())}"
        )
        return

    w = _get_width()
    tools = routine["tools"]
    title = f"{routine['icon']} {routine['label']} gestartet"

    # Fortschritt-Tracking
    results = {}
    step_status = [(display_name, False) for display_name, _, _ in tools]

    def _build_progress_panel():
        content = Text()
        for i, (name, done) in enumerate(step_status):
            icon = "✓" if done else "⏳"
            style = "green" if done else "yellow"
            content.append(f"  {icon} {name}\n", style=style)
        return Panel(
            content,
            title=title,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1),
            width=w,
        )

    # Tools sequentiell ausfuehren mit Live-Fortschritt
    with Live(_build_progress_panel(), console=bot.console.console, refresh_per_second=4) as live:
        for i, (display_name, tool_name, kwargs) in enumerate(tools):
            tool = bot.tool_registry.get_tool(tool_name)
            if tool:
                try:
                    result = await tool.execute(**kwargs)
                    results[display_name] = result
                except Exception as e:
                    results[display_name] = f"Fehler: {e}"
            else:
                results[display_name] = "Tool nicht verfuegbar"

            step_status[i] = (display_name, True)
            live.update(_build_progress_panel())

    # Ergebnisse formatieren
    scan_data = "\n\n---\n\n".join(
        f"### {name}\n{data}" for name, data in results.items()
    )

    # Analyse-Prompt mit Ergebnissen fuellen
    analysis_prompt = routine["prompt"].format(scan_data=scan_data)

    # An Claude zur Analyse schicken
    await bot.process_message(analysis_prompt)
