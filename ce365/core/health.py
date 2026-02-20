"""
CE365 Agent - Erweiterter Health Check

Vollstaendiger Selbsttest mit 9 Sektionen:
1. System-Voraussetzungen
2. Konfiguration & Berechtigungen
3. Kern-Module
4. Tool-Module Imports
5. Tool-Registry & Schema-Validierung
6. psutil Funktionstest
7. Datenbank-Verbindung
8. Netzwerk & API-Erreichbarkeit
9. LLM API Live-Test

Return-Code: 0 = OK, 1 = Fehler
"""

import sys
import shutil
import importlib
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Any

from rich.console import Console

console = Console()

# --- Helper ---

def _pass(msg: str):
    console.print(f"  [green]\u2713[/green] {msg}")

def _fail(msg: str):
    console.print(f"  [red]\u2717[/red] {msg}")

def _warn(msg: str):
    console.print(f"  [yellow]\u26a0[/yellow] {msg}")

def _detail(msg: str):
    console.print(f"    [dim]{msg}[/dim]")


# --- Sektion 1: System-Voraussetzungen ---

def _check_system(verbose: bool) -> Tuple[int, int, int]:
    console.print("[bold]1. System-Voraussetzungen[/bold]")
    passed = failed = warned = 0

    # Python-Version
    v = sys.version_info
    if v >= (3, 9):
        _pass(f"Python {v.major}.{v.minor}.{v.micro}")
        passed += 1
    else:
        _fail(f"Python {v.major}.{v.minor} (benoetigt >= 3.9)")
        failed += 1

    # Kritische Dependencies
    critical_deps = [
        ("anthropic", "Anthropic SDK"),
        ("rich", "Rich Console"),
        ("pydantic", "Pydantic"),
        ("httpx", "HTTPX"),
        ("psutil", "PSUtil"),
    ]
    for module_name, display_name in critical_deps:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "?")
            _pass(f"{display_name} ({version})")
            passed += 1
        except ImportError:
            _fail(f"{display_name} nicht installiert")
            failed += 1

    # Optionale Deps
    optional_deps = [
        ("openai", "OpenAI SDK"),
    ]
    for module_name, display_name in optional_deps:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "?")
            _pass(f"{display_name} ({version})")
            passed += 1
        except ImportError:
            _warn(f"{display_name} nicht installiert (optional)")
            warned += 1

    # Festplatte
    try:
        usage = shutil.disk_usage(Path.home())
        free_gb = usage.free / (1024 ** 3)
        if free_gb < 0.1:
            _fail(f"Festplatte: {free_gb:.1f} GB frei (< 100 MB)")
            failed += 1
        elif free_gb < 1.0:
            _warn(f"Festplatte: {free_gb:.1f} GB frei (< 1 GB)")
            warned += 1
        else:
            _pass(f"Festplatte: {free_gb:.1f} GB frei")
            passed += 1
    except Exception as e:
        _fail(f"Festplatte: {e}")
        failed += 1

    return passed, failed, warned


# --- Sektion 2: Konfiguration & Berechtigungen ---

def _check_config(verbose: bool) -> Tuple[int, int, int, Optional[Any]]:
    """Returns (passed, failed, warned, settings_or_None)"""
    console.print("\n[bold]2. Konfiguration & Berechtigungen[/bold]")
    passed = failed = warned = 0
    settings = None

    # Settings laden
    try:
        from ce365.config.settings import get_settings
        settings = get_settings()
        _pass("Settings geladen")
        passed += 1
    except Exception as e:
        _fail(f"Settings-Fehler: {e}")
        failed += 1
        return passed, failed, warned, None

    # Provider-aware Key-Check
    provider = settings.llm_provider
    key_map = {
        "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
        "openai": ("openai_api_key", "OPENAI_API_KEY"),
        "openrouter": ("openrouter_api_key", "OPENROUTER_API_KEY"),
    }
    attr, env_name = key_map.get(provider, ("anthropic_api_key", "ANTHROPIC_API_KEY"))
    api_key = getattr(settings, attr, "")
    if api_key and api_key != "test-key-not-real":
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 16 else "***"
        _pass(f"API-Key ({provider}): {masked}")
        passed += 1
    else:
        _fail(f"API-Key fuer {provider} nicht konfiguriert ({env_name})")
        failed += 1

    # Pro: Lizenzschluessel
    if settings.edition == "pro":
        if settings.license_key and settings.license_key.startswith("CE365-"):
            _pass(f"Lizenzschluessel: {settings.license_key[:12]}...")
            passed += 1
        else:
            _fail("Lizenzschluessel fehlt oder ungueltig (Format: CE365-...)")
            failed += 1

    # .env lesbar
    env_file = Path(".env")
    if env_file.exists():
        if env_file.stat().st_size > 0:
            _pass(".env vorhanden und lesbar")
            passed += 1
        else:
            _warn(".env vorhanden aber leer")
            warned += 1
    else:
        # Bei portablen Binaries ist .env optional
        if getattr(sys, "frozen", False):
            _pass(".env nicht benoetigt (portable Binary)")
            passed += 1
        else:
            _warn(".env nicht vorhanden")
            warned += 1

    # Verzeichnisse + Schreibtest
    dirs_to_check = [
        (Path("data"), "data/"),
        (Path.home() / ".ce365", "~/.ce365/"),
    ]
    for dir_path, name in dirs_to_check:
        if dir_path.exists():
            # Schreibtest
            try:
                test_file = dir_path / ".health_check_test"
                test_file.write_text("ok")
                test_file.unlink()
                _pass(f"{name} vorhanden + beschreibbar")
                passed += 1
            except Exception:
                _warn(f"{name} vorhanden, aber nicht beschreibbar")
                warned += 1
        else:
            _warn(f"{name} fehlt (wird beim Start erstellt)")
            warned += 1

    return passed, failed, warned, settings


# --- Sektion 3: Kern-Module ---

def _check_core_modules(verbose: bool) -> Tuple[int, int, int]:
    console.print("\n[bold]3. Kern-Module[/bold]")
    passed = failed = warned = 0

    core_imports = [
        ("ce365.workflow.state_machine", "WorkflowStateMachine", "WorkflowStateMachine"),
        ("ce365.tools.registry", "ToolRegistry", "ToolRegistry"),
        ("ce365.core.session", "Session", "Session"),
        ("ce365.core.providers", "create_provider", "create_provider"),
        ("ce365.core.license", "check_edition_features", "check_edition_features"),
        ("ce365.core.commands", "SlashCommandHandler", "SlashCommandHandler"),
        ("ce365.storage.changelog", "ChangelogWriter", "ChangelogWriter"),
        ("ce365.learning.case_library", "CaseLibrary", "CaseLibrary"),
        ("ce365.ui.console", "RichConsole", "RichConsole"),
    ]

    ok_count = 0
    fail_count = 0
    for module_path, class_name, display in core_imports:
        try:
            mod = importlib.import_module(module_path)
            obj = getattr(mod, class_name)
            if verbose:
                _pass(f"{display}")
            ok_count += 1
        except Exception as e:
            _fail(f"{display}: {e}")
            fail_count += 1

    if not verbose and ok_count > 0:
        _pass(f"{ok_count}/{ok_count + fail_count} Kern-Module importierbar")
    passed += ok_count
    failed += fail_count

    # Optional: PII Detection
    try:
        from ce365.security.pii_detector import PIIDetector
        _pass("PII Detection verfuegbar")
        passed += 1
    except Exception:
        _warn("PII Detection nicht verfuegbar (presidio/spacy)")
        warned += 1

    return passed, failed, warned


# --- Sektion 4: Tool-Module Imports ---

def _check_tool_imports(verbose: bool) -> Tuple[int, int, int]:
    console.print("\n[bold]4. Tool-Module[/bold]")
    passed = failed = warned = 0

    audit_modules = [
        "backup", "battery_health", "disk_health", "drivers",
        "encryption_status", "hosts_file", "incident_report", "logs",
        "malware_scan", "network_diagnostics", "network_security",
        "pdf_report", "printer_status", "processes", "reporting",
        "scheduled_tasks", "security", "software_inventory", "startup",
        "stress_tests", "system_info", "updates", "user_accounts",
        "wifi_info",
    ]

    repair_modules = [
        "backup", "browser_cleanup", "cache_rebuild", "disk_cleanup",
        "disk_optimize", "network_tools", "process_manager",
        "service_manager", "startup", "system_repair",
        "update_scheduler", "updates", "windows_update_reset",
    ]

    other_modules = [
        ("ce365.tools.analysis.root_cause", "RootCauseAnalyzer"),
        ("ce365.tools.analysis.consult_specialist", "ConsultSpecialistTool"),
        ("ce365.tools.research.web_search", "WebSearchTool"),
        ("ce365.tools.drivers.driver_manager", "DriverManager"),
    ]

    # Audit
    audit_ok = audit_fail = 0
    for mod_name in audit_modules:
        try:
            importlib.import_module(f"ce365.tools.audit.{mod_name}")
            if verbose:
                _pass(f"audit.{mod_name}")
            audit_ok += 1
        except Exception as e:
            _fail(f"audit.{mod_name}: {e}")
            audit_fail += 1

    if not verbose:
        if audit_fail == 0:
            _pass(f"Audit-Tools: {audit_ok}/{audit_ok} Module importierbar")
        else:
            _fail(f"Audit-Tools: {audit_ok}/{audit_ok + audit_fail} Module importierbar")

    passed += audit_ok
    failed += audit_fail

    # Repair
    repair_ok = repair_fail = 0
    for mod_name in repair_modules:
        try:
            importlib.import_module(f"ce365.tools.repair.{mod_name}")
            if verbose:
                _pass(f"repair.{mod_name}")
            repair_ok += 1
        except Exception as e:
            _fail(f"repair.{mod_name}: {e}")
            repair_fail += 1

    if not verbose:
        if repair_fail == 0:
            _pass(f"Repair-Tools: {repair_ok}/{repair_ok} Module importierbar")
        else:
            _fail(f"Repair-Tools: {repair_ok}/{repair_ok + repair_fail} Module importierbar")

    passed += repair_ok
    failed += repair_fail

    # Analyse/Research/Drivers
    other_ok = other_fail = 0
    for mod_path, cls_name in other_modules:
        try:
            mod = importlib.import_module(mod_path)
            getattr(mod, cls_name)
            if verbose:
                _pass(f"{mod_path.split('.')[-1]}.{cls_name}")
            other_ok += 1
        except Exception as e:
            _fail(f"{cls_name}: {e}")
            other_fail += 1

    if not verbose:
        if other_fail == 0:
            _pass(f"Analyse/Research: {other_ok}/{other_ok} Module importierbar")
        else:
            _fail(f"Analyse/Research: {other_ok}/{other_ok + other_fail} Module importierbar")

    passed += other_ok
    failed += other_fail

    return passed, failed, warned


# --- Sektion 5: Tool-Registry & Schema-Validierung ---

def _check_tool_registry(verbose: bool) -> Tuple[int, int, int]:
    console.print("\n[bold]5. Tool-Registry & Schema[/bold]")
    passed = failed = warned = 0

    try:
        from ce365.tools.registry import ToolRegistry
        from ce365.tools.base import BaseTool, AuditTool, RepairTool

        registry = ToolRegistry()
        registered = 0
        schema_errors = 0
        audit_count = 0
        repair_count = 0

        # Alle Tool-Module durchsuchen und Tool-Klassen finden
        tool_packages = [
            ("ce365.tools.audit", [
                "backup", "battery_health", "disk_health", "drivers",
                "encryption_status", "hosts_file", "logs",
                "malware_scan", "network_diagnostics", "network_security",
                "pdf_report", "printer_status", "processes", "reporting",
                "scheduled_tasks", "security", "software_inventory", "startup",
                "stress_tests", "system_info", "updates", "user_accounts",
                "wifi_info",
            ]),
            ("ce365.tools.repair", [
                "backup", "browser_cleanup", "cache_rebuild", "disk_cleanup",
                "disk_optimize", "network_tools", "process_manager",
                "service_manager", "startup", "system_repair",
                "update_scheduler", "updates", "windows_update_reset",
            ]),
            ("ce365.tools.analysis", ["root_cause", "consult_specialist"]),
            ("ce365.tools.research", ["web_search"]),
            ("ce365.tools.drivers", ["driver_manager"]),
        ]

        for pkg, modules in tool_packages:
            for mod_name in modules:
                try:
                    mod = importlib.import_module(f"{pkg}.{mod_name}")
                    for attr_name in dir(mod):
                        obj = getattr(mod, attr_name)
                        if (isinstance(obj, type)
                                and issubclass(obj, BaseTool)
                                and obj not in (BaseTool, AuditTool, RepairTool)
                                and not getattr(obj, '__abstractmethods__', None)):
                            try:
                                # IncidentReportTool braucht Konstruktor-Argumente
                                if "IncidentReport" in attr_name:
                                    if verbose:
                                        _pass(f"{attr_name} (nur Import)")
                                    registered += 1
                                    if issubclass(obj, AuditTool):
                                        audit_count += 1
                                    elif issubclass(obj, RepairTool):
                                        repair_count += 1
                                    continue

                                instance = obj()
                                schema = instance.to_anthropic_tool()

                                # Schema validieren
                                if not schema.get("name"):
                                    _fail(f"{attr_name}: name fehlt")
                                    schema_errors += 1
                                    continue
                                if not schema.get("description"):
                                    _fail(f"{attr_name}: description fehlt")
                                    schema_errors += 1
                                    continue
                                if not isinstance(schema.get("input_schema"), dict):
                                    _fail(f"{attr_name}: input_schema fehlt/ungueltig")
                                    schema_errors += 1
                                    continue

                                registry.register(instance)
                                registered += 1
                                if issubclass(obj, AuditTool):
                                    audit_count += 1
                                elif issubclass(obj, RepairTool):
                                    repair_count += 1

                                if verbose:
                                    _pass(f"{schema['name']}")
                            except Exception as e:
                                if verbose:
                                    _fail(f"{attr_name}: {e}")
                                schema_errors += 1
                except Exception:
                    pass  # Modul-Import schon in Sektion 4 geprueft

        if registered > 0:
            if not verbose:
                _pass(f"{registered} Tools registriert ({audit_count} Audit, {repair_count} Repair)")
            passed += registered
        else:
            _fail("Keine Tools registrierbar")
            failed += 1

        if schema_errors > 0:
            _warn(f"{schema_errors} Tools mit Schema-Fehlern")
            warned += schema_errors

    except Exception as e:
        _fail(f"Registry-Fehler: {e}")
        failed += 1

    return passed, failed, warned


# --- Sektion 6: psutil Funktionstest ---

def _check_psutil(verbose: bool) -> Tuple[int, int, int]:
    console.print("\n[bold]6. psutil Funktionstest[/bold]")
    passed = failed = warned = 0

    try:
        import psutil

        # CPU
        cpu = psutil.cpu_percent(interval=0.1)
        _pass(f"CPU: {cpu}%")
        passed += 1

        # RAM
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_pct = mem.percent
        _pass(f"RAM: {used_pct}% von {total_gb:.1f} GB belegt")
        passed += 1

        # Disk
        disk = psutil.disk_usage("/")
        disk_free_gb = disk.free / (1024 ** 3)
        _pass(f"Disk /: {disk_free_gb:.1f} GB frei ({disk.percent}% belegt)")
        passed += 1

        # Prozesse
        pids = psutil.pids()
        _pass(f"Prozesse: {len(pids)} aktiv")
        passed += 1

    except ImportError:
        _fail("psutil nicht installiert")
        failed += 1
    except Exception as e:
        _fail(f"psutil-Fehler: {e}")
        failed += 1

    return passed, failed, warned


# --- Sektion 7: Datenbank-Verbindung ---

def _check_database(verbose: bool, settings: Optional[Any]) -> Tuple[int, int, int]:
    console.print("\n[bold]7. Datenbank[/bold]")
    passed = failed = warned = 0

    if settings is None:
        _warn("Uebersprungen (keine Settings)")
        warned += 1
        return passed, failed, warned

    db_type = getattr(settings, "learning_db_type", "sqlite")

    if db_type == "sqlite":
        import sqlite3
        db_path = Path(getattr(settings, "learning_db_fallback", "data/cases.db"))
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                conn.execute("SELECT 1")
                conn.close()
                _pass(f"SQLite: {db_path.name} erreichbar")
                passed += 1
            except Exception as e:
                _fail(f"SQLite: {e}")
                failed += 1
        else:
            _warn(f"SQLite: {db_path} nicht vorhanden (wird beim Start erstellt)")
            warned += 1
    else:
        # PostgreSQL / MySQL
        db_url = getattr(settings, "learning_db_url", "")
        if not db_url:
            _warn(f"{db_type}: Keine DB-URL konfiguriert")
            warned += 1
        else:
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(db_url, connect_args={"connect_timeout": 5} if "mysql" in db_url or "postgresql" in db_url else {})
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                _pass(f"{db_type}: Verbindung OK")
                passed += 1
                engine.dispose()
            except Exception as e:
                _fail(f"{db_type}: {e}")
                failed += 1

    return passed, failed, warned


# --- Sektion 8: Netzwerk & API-Erreichbarkeit ---

def _check_network(verbose: bool, settings: Optional[Any]) -> Tuple[int, int, int]:
    console.print("\n[bold]8. Netzwerk & API[/bold]")
    passed = failed = warned = 0

    if settings is None:
        _warn("Uebersprungen (keine Settings)")
        warned += 1
        return passed, failed, warned

    provider = getattr(settings, "llm_provider", "anthropic")

    # Provider-spezifischer API-Ping
    ping_targets = {
        "anthropic": (
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": "ping", "anthropic-version": "2023-06-01"},
            "Anthropic API",
        ),
        "openai": (
            "https://api.openai.com/v1/models",
            {"Authorization": "Bearer ping"},
            "OpenAI API",
        ),
        "openrouter": (
            "https://openrouter.ai/api/v1/models",
            {"Authorization": "Bearer ping"},
            "OpenRouter API",
        ),
    }

    target = ping_targets.get(provider, ping_targets["anthropic"])
    url, headers, name = target

    try:
        import httpx
        response = httpx.get(url, headers=headers, timeout=5)
        # 401/400 = API erreichbar (ungueltige Credentials sind egal)
        if response.status_code in (401, 400, 403, 405, 200):
            _pass(f"{name} erreichbar")
            passed += 1
        else:
            _warn(f"{name}: HTTP {response.status_code}")
            warned += 1
    except Exception as e:
        _fail(f"{name} nicht erreichbar: {e}")
        failed += 1

    # Pro: Lizenzserver
    if settings.edition == "pro" and settings.license_server_url:
        try:
            import httpx
            ls_url = settings.license_server_url.rstrip("/") + "/health"
            response = httpx.get(ls_url, timeout=5)
            if response.status_code == 200:
                _pass("Lizenzserver erreichbar")
                passed += 1
            else:
                _warn(f"Lizenzserver: HTTP {response.status_code}")
                warned += 1
        except Exception as e:
            _warn(f"Lizenzserver nicht erreichbar: {e}")
            warned += 1

    return passed, failed, warned


# --- Sektion 9: LLM API Live-Test ---

def _check_llm_api(verbose: bool, settings: Optional[Any]) -> Tuple[int, int, int]:
    console.print("\n[bold]9. LLM API Live-Test[/bold]")
    passed = failed = warned = 0

    if settings is None:
        _warn("Uebersprungen (keine Settings)")
        warned += 1
        return passed, failed, warned

    provider_name = getattr(settings, "llm_provider", "anthropic")
    model = getattr(settings, "llm_model", None)

    # Key ermitteln
    key_map = {
        "anthropic": "anthropic_api_key",
        "openai": "openai_api_key",
        "openrouter": "openrouter_api_key",
    }
    api_key = getattr(settings, key_map.get(provider_name, "anthropic_api_key"), "")

    if not api_key or api_key == "test-key-not-real":
        _warn("Uebersprungen (kein API-Key)")
        warned += 1
        return passed, failed, warned

    try:
        from ce365.core.providers import create_provider

        provider = create_provider(provider_name, api_key, model)
        response = provider.create_message(
            messages=[{"role": "user", "content": "Hi"}],
            system="Reply with OK.",
            max_tokens=10,
        )

        # Antwort auswerten
        if response:
            model_used = model or provider_name
            _pass(f"LLM antwortet ({provider_name}/{model_used})")
            passed += 1

            if verbose and hasattr(response, "usage"):
                usage = response.usage
                input_t = getattr(usage, "input_tokens", "?")
                output_t = getattr(usage, "output_tokens", "?")
                _detail(f"Tokens: {input_t} input, {output_t} output")
        else:
            _fail("LLM: Leere Antwort")
            failed += 1

    except Exception as e:
        _fail(f"LLM-Fehler: {e}")
        failed += 1

    return passed, failed, warned


# --- Orchestrator ---

def run_health_check(verbose: bool = False) -> int:
    """
    Fuehrt den erweiterten Health-Check durch.

    Args:
        verbose: Zeigt Details zu jedem einzelnen Tool/Modul

    Returns:
        0 = alles OK, 1 = Fehler gefunden
    """
    from ce365.__version__ import __version__

    console.print(f"\n[bold cyan]\U0001fa7a CE365 Health-Check v{__version__}[/bold cyan]")
    if verbose:
        console.print("[dim]Verbose-Modus aktiv[/dim]")
    console.print()

    total_passed = 0
    total_failed = 0
    total_warned = 0

    # Sektion 1: System
    p, f, w = _check_system(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 2: Config (gibt settings zurueck)
    p, f, w, settings = _check_config(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 3: Kern-Module
    p, f, w = _check_core_modules(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 4: Tool-Module
    p, f, w = _check_tool_imports(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 5: Tool-Registry
    p, f, w = _check_tool_registry(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 6: psutil
    p, f, w = _check_psutil(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 7: Datenbank
    p, f, w = _check_database(verbose, settings)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 8: Netzwerk
    p, f, w = _check_network(verbose, settings)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 9: LLM Live-Test
    p, f, w = _check_llm_api(verbose, settings)
    total_passed += p; total_failed += f; total_warned += w

    # Zusammenfassung
    console.print()
    console.print("[bold]Zusammenfassung[/bold]")
    total = total_passed + total_failed + total_warned
    console.print(f"  [green]\u2713 {total_passed} bestanden[/green]  "
                  f"[red]\u2717 {total_failed} fehlgeschlagen[/red]  "
                  f"[yellow]\u26a0 {total_warned} Warnungen[/yellow]  "
                  f"[dim]({total} gesamt)[/dim]")
    console.print()

    if total_failed == 0:
        console.print(f"[bold green]\u2705 Health-Check bestanden[/bold green]\n")
        return 0
    else:
        console.print(f"[bold red]\u274c {total_failed} Fehler gefunden[/bold red]\n")
        return 1
