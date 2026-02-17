#!/usr/bin/env python3
"""
Test-Skript für Learning System
"""

import asyncio
from ce365.learning.case_library import CaseLibrary, Case
from ce365.ui.console import RichConsole

console = RichConsole()


async def test_case_library():
    """Case Library testen"""

    print("\n" + "="*80)
    print("  LEARNING SYSTEM TEST")
    print("="*80 + "\n")

    # Case Library erstellen
    case_lib = CaseLibrary(db_path="data/test_cases.db")
    console.display_success("✓ Case Library initialisiert")

    # Test Case 1: Windows Update Problem
    print("\n1. TEST CASE ERSTELLEN (Windows Update)")
    print("-" * 80)

    case1 = Case(
        os_type="windows",
        os_version="Windows 11",
        problem_description="Windows Update Fehler 0x80070002, Update lädt nicht",
        error_codes="0x80070002",
        root_cause="Windows Update Service gestoppt und Cache korrupt",
        solution_plan="""Schritt 1: Windows Update Service neustarten
Schritt 2: SoftwareDistribution Cache leeren""",
        executed_steps='["restart_service", "clear_cache"]',
        success=True,
        session_id="test-session-001",
        tokens_used=3500,
        duration_minutes=12
    )

    case1_id = case_lib.save_case(case1)
    console.display_success(f"✓ Case 1 gespeichert (ID: {case1_id})")

    # Test Case 2: macOS DNS Problem
    print("\n2. TEST CASE ERSTELLEN (macOS DNS)")
    print("-" * 80)

    case2 = Case(
        os_type="macos",
        os_version="macOS 15 Sequoia",
        problem_description="Websites laden nicht, WLAN verbunden aber kein Internet",
        root_cause="DNS Cache korrupt",
        solution_plan="Schritt 1: DNS Cache leeren mit dscacheutil -flushcache",
        executed_steps='["flush_dns"]',
        success=True,
        session_id="test-session-002",
        tokens_used=2800,
        duration_minutes=5
    )

    case2_id = case_lib.save_case(case2)
    console.display_success(f"✓ Case 2 gespeichert (ID: {case2_id})")

    # Test Case 3: Drucker Problem
    print("\n3. TEST CASE ERSTELLEN (Drucker Spooler)")
    print("-" * 80)

    case3 = Case(
        os_type="windows",
        os_version="Windows 11",
        problem_description="Druckaufträge hängen, Drucker druckt nicht",
        root_cause="Print Spooler Service hängt, Warteschlange blockiert",
        solution_plan="""Schritt 1: Spooler Service stoppen
Schritt 2: Warteschlange leeren
Schritt 3: Spooler Service starten""",
        executed_steps='["stop_spooler", "clear_queue", "start_spooler"]',
        success=True,
        session_id="test-session-003",
        tokens_used=4200,
        duration_minutes=8
    )

    case3_id = case_lib.save_case(case3)
    console.display_success(f"✓ Case 3 gespeichert (ID: {case3_id})")

    # Ähnlichkeitssuche testen
    print("\n4. ÄHNLICHKEITSSUCHE TESTEN")
    print("-" * 80)

    # Suche nach Windows Update Problem
    print("\nSuche: 'Windows Update funktioniert nicht, Fehler 0x80070002'")
    similar = case_lib.find_similar_cases(
        os_type="windows",
        problem_description="Windows Update funktioniert nicht, Fehler 0x80070002",
        error_code="0x80070002",
        limit=3
    )

    if similar:
        console.display_success(f"✓ {len(similar)} ähnliche Fälle gefunden")
        for case, similarity in similar:
            print(f"\n  Match: {similarity*100:.0f}% Ähnlichkeit")
            print(f"  Problem: {case.problem_description[:60]}...")
            print(f"  Lösung: {case.solution_plan[:60]}...")
    else:
        console.display_warning("Keine ähnlichen Fälle gefunden")

    # Suche nach macOS DNS Problem
    print("\n\nSuche: 'macOS Internet langsam, Websites laden nicht'")
    similar = case_lib.find_similar_cases(
        os_type="macos",
        problem_description="macOS Internet langsam, Websites laden nicht",
        limit=3
    )

    if similar:
        console.display_success(f"✓ {len(similar)} ähnliche Fälle gefunden")
        for case, similarity in similar:
            print(f"\n  Match: {similarity*100:.0f}% Ähnlichkeit")
            print(f"  Problem: {case.problem_description[:60]}...")
            print(f"  Lösung: {case.solution_plan[:60]}...")

    # Wiederverwendung testen
    print("\n\n5. WIEDERVERWENDUNG TESTEN")
    print("-" * 80)

    # Fall 1 mehrmals als wiederverwendet markieren
    case_lib.mark_case_reused(case1_id, success=True)
    case_lib.mark_case_reused(case1_id, success=True)
    case_lib.mark_case_reused(case1_id, success=True)

    reused_case = case_lib.get_case_by_id(case1_id)
    console.display_success(
        f"✓ Case {case1_id}: {reused_case.reuse_count}x wiederverwendet, "
        f"{reused_case.success_rate*100:.0f}% Erfolgsquote"
    )

    # Statistiken
    print("\n6. STATISTIKEN")
    print("-" * 80)

    stats = case_lib.get_statistics()
    console.display_learning_stats(stats)

    # UI-Test: Bekannte Lösung anzeigen
    print("\n7. UI-TEST: BEKANNTE LÖSUNG")
    print("-" * 80)

    case_data = {
        'problem_description': reused_case.problem_description,
        'root_cause': reused_case.root_cause,
        'solution_plan': reused_case.solution_plan,
        'reuse_count': reused_case.reuse_count,
        'success_rate': reused_case.success_rate
    }

    console.display_known_solution(case_data, similarity=0.95)

    print("\n" + "="*80)
    print("  TEST ABGESCHLOSSEN")
    print("="*80)
    print()

    # Cleanup Info
    print(f"Test-Datenbank: data/test_cases.db")
    print(f"Zum Löschen: rm data/test_cases.db")
    print()


if __name__ == "__main__":
    asyncio.run(test_case_library())
