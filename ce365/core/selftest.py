"""
CE365 Agent - Integrations-Selftest

Fuehrt echte Tool-Aufrufe, PDF-Generierung, DB-Roundtrips und
LLM Tool-Use durch — schliesst die Luecke zwischen "importierbar" (--health)
und "funktioniert tatsaechlich" (--selftest).

5 Sektionen:
1. Tool-Ausfuehrung (SystemInfo, Prozesse, DiskHealth)
2. PDF-Generierung mit Emojis/Umlauten
3. Datenbank-Roundtrip (Case schreiben/lesen/loeschen)
4. LLM Tool-Use Roundtrip
5. Session-Roundtrip
"""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import Tuple

from rich.console import Console

console = Console()


# --- Helper (gleicher Stil wie health.py) ---

def _pass(msg: str):
    console.print(f"  [green]\u2713[/green] {msg}")

def _fail(msg: str):
    console.print(f"  [red]\u2717[/red] {msg}")

def _warn(msg: str):
    console.print(f"  [yellow]\u26a0[/yellow] {msg}")

def _detail(msg: str):
    console.print(f"    [dim]{msg}[/dim]")


# --- Sektion 1: Tool-Ausfuehrung ---

async def _test_tools(verbose: bool) -> Tuple[int, int, int]:
    console.print("[bold]1. Tool-Ausfuehrung[/bold]")
    passed = failed = warned = 0

    tools_to_test = [
        ("SystemInfoTool", "ce365.tools.audit.system_info", "SystemInfoTool", {}),
        ("CheckRunningProcessesTool", "ce365.tools.audit.processes", "CheckRunningProcessesTool", {"sort_by": "cpu", "limit": 5}),
        ("DiskHealthTool", "ce365.tools.audit.disk_health", "DiskHealthTool", {}),
    ]

    for label, module_path, class_name, kwargs in tools_to_test:
        try:
            import importlib
            mod = importlib.import_module(module_path)
            tool_cls = getattr(mod, class_name)
            tool = tool_cls()

            if kwargs:
                result = await tool.execute(**kwargs)
            else:
                result = await tool.execute()

            if isinstance(result, str) and len(result) > 20 and "\u274c" not in result:
                _pass(f"{label} — {len(result)} Zeichen")
                passed += 1
                if verbose:
                    lines = result.strip().split("\n")[:3]
                    for line in lines:
                        _detail(line[:120])
            else:
                _fail(f"{label} — Ergebnis zu kurz oder Fehler-Marker")
                failed += 1
                if verbose and isinstance(result, str):
                    _detail(result[:200])

        except Exception as e:
            _fail(f"{label} — {e}")
            failed += 1

    return passed, failed, warned


# --- Sektion 2: PDF-Generierung ---

def _test_pdf(verbose: bool) -> Tuple[int, int, int]:
    console.print("[bold]2. PDF-Generierung[/bold]")
    passed = failed = warned = 0

    tmp_path = None
    try:
        from ce365.tools.audit.pdf_report import generate_pdf_report

        # Test-Daten mit Emojis + Umlauten (Regression-Test)
        report_data = {
            "system_info": "Host: Selftest-PC \u00f6\u00e4\u00fc\u00df\nOS: macOS 15.0\nCPU: Apple M1",
            "findings": [
                {"priority": "info", "title": "Testbefund \u2705", "detail": "Alles in Ordnung \u00fc\u00e4\u00f6"},
                {"priority": "warning", "title": "\u26a0 Warnung mit Emoji \U0001f525", "detail": "Speicher knapp"},
            ],
            "recommendations": "Regelm\u00e4\u00dfige Wartung durchf\u00fchren \U0001f527\nUpdates installieren",
        }

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(tmp_fd)

        result_path = generate_pdf_report(
            report_data=report_data,
            technician="Selftest-Techniker",
            company="Test GmbH \u00d6sterreich",
            output_path=Path(tmp_path),
        )

        pdf_file = Path(result_path)
        if pdf_file.exists() and pdf_file.stat().st_size > 500:
            _pass(f"PDF erstellt — {pdf_file.stat().st_size:,} Bytes")
            passed += 1
            if verbose:
                _detail(f"Pfad: {result_path}")
        else:
            _fail(f"PDF zu klein oder nicht erstellt ({pdf_file.stat().st_size if pdf_file.exists() else 0} Bytes)")
            failed += 1

    except Exception as e:
        _fail(f"PDF-Generierung — {e}")
        failed += 1

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return passed, failed, warned


# --- Sektion 3: Datenbank-Roundtrip ---

def _test_database(verbose: bool, settings) -> Tuple[int, int, int]:
    console.print("[bold]3. Datenbank-Roundtrip[/bold]")
    passed = failed = warned = 0

    if settings is None:
        _warn("Uebersprungen — keine Konfiguration")
        return passed, failed, warned + 1

    test_session_id = f"selftest-{uuid.uuid4().hex[:12]}"
    case_id = None

    try:
        from ce365.learning.case_library import CaseLibrary, Case
        from ce365.learning.database import CaseModel

        lib = CaseLibrary()

        # save_case
        test_case = Case(
            os_type="selftest",
            os_version="1.0",
            problem_description=f"Selftest Roundtrip {test_session_id}",
            session_id=test_session_id,
            success=True,
        )
        case_id = lib.save_case(test_case)

        if isinstance(case_id, int) and case_id > 0:
            _pass(f"save_case — ID {case_id}")
            passed += 1
        else:
            _fail(f"save_case — unerwarteter Rueckgabewert: {case_id}")
            failed += 1

        # get_case_by_id
        loaded = lib.get_case_by_id(case_id)
        if loaded and loaded.problem_description == test_case.problem_description:
            _pass("get_case_by_id — Daten korrekt")
            passed += 1
        else:
            _fail("get_case_by_id — Case nicht gefunden oder Daten falsch")
            failed += 1

        # get_statistics
        stats = lib.get_statistics()
        if isinstance(stats, dict) and "total_cases" in stats:
            _pass(f"get_statistics — {stats['total_cases']} Cases gesamt")
            passed += 1
            if verbose:
                _detail(f"Erfolgsrate: {stats.get('avg_success_rate', 0):.0%}")
        else:
            _fail("get_statistics — unerwartetes Format")
            failed += 1

    except Exception as e:
        _fail(f"Datenbank — {e}")
        failed += 1

    finally:
        # Aufraumen: Test-Case loeschen
        if case_id is not None:
            try:
                from ce365.learning.database import get_db_manager, CaseModel
                db_manager = get_db_manager()
                session = db_manager.get_session()
                try:
                    row = session.query(CaseModel).filter(CaseModel.id == case_id).first()
                    if row:
                        session.delete(row)
                        session.commit()
                        if verbose:
                            _detail(f"Test-Case {case_id} geloescht")
                except Exception:
                    session.rollback()
                finally:
                    session.close()
            except Exception:
                pass  # Cleanup best-effort

    return passed, failed, warned


# --- Sektion 4: LLM Tool-Use Roundtrip ---

def _test_llm_tool_use(verbose: bool, settings) -> Tuple[int, int, int]:
    console.print("[bold]4. LLM Tool-Use Roundtrip[/bold]")
    passed = failed = warned = 0

    if settings is None:
        _warn("Uebersprungen — keine Konfiguration")
        return passed, failed, warned + 1

    # API-Key vorhanden?
    key_map = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    api_key = key_map.get(settings.llm_provider, "")
    if not api_key:
        _warn(f"Uebersprungen — kein API-Key fuer {settings.llm_provider}")
        return passed, failed, warned + 1

    try:
        from ce365.core.providers import create_provider

        provider = create_provider(settings.llm_provider, api_key, settings.llm_model)

        ping_tool = {
            "name": "selftest_ping",
            "description": "Returns pong. Always use this tool when asked.",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }

        response = provider.create_message(
            messages=[{"role": "user", "content": "Use the selftest_ping tool."}],
            system="Always use the selftest_ping tool. Do not say anything, just use the tool.",
            tools=[ping_tool],
            max_tokens=100,
        )

        # Antwort pruefen — je nach Provider unterschiedliche Formate
        tool_used = False
        tool_name = None

        # Anthropic-Format
        if hasattr(response, "content"):
            for block in response.content:
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_used = True
                    tool_name = block.name
                    break

        # OpenAI-Format
        if not tool_used and hasattr(response, "choices"):
            for choice in response.choices:
                msg = choice.message
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_used = True
                    tool_name = msg.tool_calls[0].function.name
                    break

        if tool_used and tool_name == "selftest_ping":
            _pass(f"Tool-Use erkannt — {tool_name}")
            passed += 1
        elif tool_used:
            _warn(f"Tool-Use erkannt, aber Name unerwartet: {tool_name}")
            warned += 1
        else:
            _fail("Kein Tool-Use in LLM-Antwort")
            failed += 1

        # Token-Info bei verbose
        if verbose:
            if hasattr(response, "usage"):
                usage = response.usage
                input_t = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None) or "?"
                output_t = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None) or "?"
                _detail(f"Tokens: {input_t} input, {output_t} output")

    except Exception as e:
        _fail(f"LLM Tool-Use — {e}")
        failed += 1

    return passed, failed, warned


# --- Sektion 5: Session-Roundtrip ---

def _test_session(verbose: bool) -> Tuple[int, int, int]:
    console.print("[bold]5. Session-Roundtrip[/bold]")
    passed = failed = warned = 0

    try:
        from ce365.core.session import Session

        sess = Session()

        # Messages hinzufuegen
        sess.add_message("user", "test")
        sess.add_message("assistant", "ok")

        # get_messages
        messages = sess.get_messages()
        if len(messages) == 2 and messages[0]["role"] == "user" and messages[1]["role"] == "assistant":
            _pass("add_message + get_messages — 2 Messages korrekt")
            passed += 1
        else:
            _fail(f"get_messages — erwartet 2, bekommen {len(messages)}")
            failed += 1

        # get_last_message
        last = sess.get_last_message()
        if last and last["role"] == "assistant":
            _pass("get_last_message — role=assistant")
            passed += 1
        else:
            _fail(f"get_last_message — unerwartet: {last}")
            failed += 1

        # clear_messages
        sess.clear_messages()
        if len(sess.get_messages()) == 0:
            _pass("clear_messages — Liste leer")
            passed += 1
        else:
            _fail("clear_messages — Liste nicht leer")
            failed += 1

        if verbose:
            _detail(f"Session-ID: {sess.session_id}")

    except Exception as e:
        _fail(f"Session — {e}")
        failed += 1

    return passed, failed, warned


# --- Orchestrator ---

def run_selftest(verbose: bool = False) -> int:
    """
    Fuehrt den Integrations-Selftest durch.

    Startet zuerst den Health-Check — wenn der fehlschlaegt, wird der
    Selftest nicht durchgefuehrt.

    Returns:
        0 = alles OK, 1 = Fehler gefunden
    """
    from ce365.__version__ import __version__
    from ce365.core.health import run_health_check

    # Health-Check zuerst
    console.print(f"\n[bold cyan]\U0001f9ea CE365 Integrations-Selftest v{__version__}[/bold cyan]")
    console.print("[dim]Phase 1: Health-Check[/dim]\n")

    health_result = run_health_check(verbose=verbose)

    if health_result != 0:
        console.print("\n[bold red]\u274c Health-Check fehlgeschlagen — Selftest abgebrochen[/bold red]")
        console.print("[dim]Behebe zuerst die Health-Check-Fehler.[/dim]\n")
        return 1

    # Settings laden
    settings = None
    try:
        from ce365.config.settings import get_settings
        settings = get_settings()
    except Exception:
        pass

    # Selftest-Sektionen
    console.print(f"\n[bold cyan]\U0001f9ea Phase 2: Integrations-Tests[/bold cyan]")
    if verbose:
        console.print("[dim]Verbose-Modus aktiv[/dim]")
    console.print()

    total_passed = 0
    total_failed = 0
    total_warned = 0

    # Sektion 1: Tools (async)
    p, f, w = asyncio.run(_test_tools(verbose))
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 2: PDF
    p, f, w = _test_pdf(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 3: Datenbank
    p, f, w = _test_database(verbose, settings)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 4: LLM Tool-Use
    p, f, w = _test_llm_tool_use(verbose, settings)
    total_passed += p; total_failed += f; total_warned += w

    # Sektion 5: Session
    p, f, w = _test_session(verbose)
    total_passed += p; total_failed += f; total_warned += w

    # Zusammenfassung
    console.print()
    console.print("[bold]Zusammenfassung Selftest[/bold]")
    total = total_passed + total_failed + total_warned
    console.print(f"  [green]\u2713 {total_passed} bestanden[/green]  "
                  f"[red]\u2717 {total_failed} fehlgeschlagen[/red]  "
                  f"[yellow]\u26a0 {total_warned} Warnungen[/yellow]  "
                  f"[dim]({total} gesamt)[/dim]")
    console.print()

    if total_failed == 0:
        console.print("[bold green]\u2705 Selftest bestanden[/bold green]\n")
        return 0
    else:
        console.print(f"[bold red]\u274c {total_failed} Fehler im Selftest[/bold red]\n")
        return 1
