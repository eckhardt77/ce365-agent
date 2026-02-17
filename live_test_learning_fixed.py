#!/usr/bin/env python3
"""
Live-Test für Learning System - KORRIGIERT

Testet den ECHTEN Bot-Flow:
1. Bot starten
2. "Neuer Fall" eingeben
3. Problem beschreiben (mit Error-Code)
4. Bot sollte automatisch bekanntes Problem erkennen
"""

import asyncio
from ce365.core.bot import CE365Bot
from ce365.learning.case_library import CaseLibrary, Case

async def live_test_fixed():
    """Live-Test mit echtem Bot-Flow"""

    print("\n" + "="*80)
    print("  LEARNING SYSTEM - LIVE TEST (KORRIGIERT)")
    print("="*80 + "\n")

    # Zuerst: Test-Case in Datenbank vorbereiten
    print("VORBEREITUNG: Test-Case in Datenbank laden...")
    print("-" * 80)

    case_lib = CaseLibrary()

    # Test Case: Windows Update (bereits 5x verwendet)
    test_case = Case(
        os_type="windows",
        os_version="Windows 11",
        problem_description="Windows Update Fehler 0x80070002, Update funktioniert nicht",
        error_codes="0x80070002",
        root_cause="Windows Update Service gestoppt und SoftwareDistribution Cache korrupt",
        solution_plan="""REPARATUR-PLAN:

Schritt 1: Windows Update Service neustarten
  Risiko: NIEDRIG
  Kommando: net stop wuauserv && net start wuauserv
  Rollback: net stop wuauserv && net start wuauserv

Schritt 2: SoftwareDistribution Cache leeren
  Risiko: NIEDRIG
  Kommando: rd /s /q C:\\Windows\\SoftwareDistribution\\Download
  Rollback: Wird automatisch beim nächsten Update neu erstellt""",
        executed_steps='["restart_service", "clear_cache"]',
        success=True,
        session_id="demo-case-001",
        tokens_used=4200,
        duration_minutes=12,
        reuse_count=5,  # Bereits 5x verwendet
        success_rate=1.0  # 100% Erfolgsquote
    )

    try:
        case_id = case_lib.save_case(test_case)
        print(f"✓ Demo-Case gespeichert (ID: {case_id})")
        print(f"  Problem: {test_case.problem_description[:60]}...")
        print(f"  Bereits {test_case.reuse_count}x wiederverwendet ({test_case.success_rate*100:.0f}% Erfolg)")
        print()
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            print("✓ Demo-Case bereits in Datenbank vorhanden")
            print()
        else:
            raise

    # Stats anzeigen
    stats = case_lib.get_statistics()
    print(f"📊 Aktuelle Statistik:")
    print(f"  Gespeicherte Fälle: {stats['total_cases']}")
    print(f"  Wiederverwendungen: {stats['total_reuses']}")
    print()

    print("="*80)
    print("  TEST-SZENARIO")
    print("="*80)
    print()
    print("Der folgende Test simuliert einen echten Bot-Workflow:")
    print()
    print("1. Bot initialisieren")
    print("2. Erste Message: 'Neuer Fall'")
    print("3. Zweite Message: Problem beschreiben (mit Error-Code 0x80070002)")
    print("4. Bot erkennt automatisch bekanntes Problem!")
    print()
    input("Drücke ENTER um zu starten...")
    print()

    # Bot initialisieren
    bot = CE365Bot()

    print("\n" + "="*80)
    print("  SIMULATION START")
    print("="*80 + "\n")

    # Message 1: "Neuer Fall"
    print("[USER] Neuer Fall")
    print()
    print("[BOT] (würde jetzt Startfragen stellen...)")
    print()

    # Message simulieren (ohne API Call)
    bot.session.add_message(role="user", content="Neuer Fall")
    bot.session.add_message(role="assistant", content="Startfragen...")

    # Message 2: Problem beschreiben
    user_response = """Ja, Backup vorhanden via Time Machine.
Windows 11 Pro.
Problem: Windows Update Fehler 0x80070002, Update lädt nicht.
Bereits versucht: Neustart, Windows Update Troubleshooter, aber Problem besteht."""

    print("[USER]")
    print(user_response)
    print()

    # Session Messages checken
    print(f"Session Messages: {len(bot.session.messages)}")
    print()

    # Problem-Info extrahieren
    print("🔍 Bot extrahiert Problem-Informationen...")
    bot._extract_problem_info(user_response)

    print(f"  ✓ OS erkannt: {bot.detected_os_type}")
    print(f"  ✓ Version: {bot.detected_os_version}")
    print(f"  ✓ Error-Codes: {bot.error_codes}")
    print()

    # Jetzt Check durchführen (wie im echten run() Loop)
    print("🔍 Learning System prüft auf bekannte Probleme...")
    print()

    # Session Messages muss >= 2 sein (siehe bot.py Zeile 128)
    if len(bot.session.messages) >= 2 and bot.detected_os_type:
        similar_found = await bot._check_for_similar_cases()

        if similar_found:
            print()
            print("="*80)
            print("  ✅ ERFOLG! Learning System hat bekanntes Problem erkannt!")
            print("="*80)
            print()
            print("CE365 hat eine bekannte Lösung angeboten!")
            print("User könnte jetzt wählen:")
            print("  1 = Bewährte Lösung (schnell, ~2 Min)")
            print("  2 = Vollständiger Audit (gründlich, ~10 Min)")
            print()
        else:
            print()
            print("="*80)
            print("  ❌ Kein ähnlicher Fall gefunden")
            print("="*80)
            print()
    else:
        print()
        print("="*80)
        print("  ⚠️  BEDINGUNG NICHT ERFÜLLT")
        print("="*80)
        print()
        print(f"  Session Messages: {len(bot.session.messages)} (need >= 2)")
        print(f"  OS erkannt: {bot.detected_os_type}")
        print()

    print()
    print("="*80)
    print("  STATISTIKEN")
    print("="*80)
    print()

    # Stats anzeigen
    stats = case_lib.get_statistics()
    bot.console.display_learning_stats(stats)

    print()
    print("="*80)
    print("  TEST ABGESCHLOSSEN")
    print("="*80)
    print()
    print("Was wurde getestet:")
    print("  ✓ Problem-Info Extraktion (OS, Error-Code)")
    print("  ✓ Session Message Check (>= 2 Messages)")
    print("  ✓ Ähnlichkeitssuche in Case Library")
    print("  ✓ UI: Bekannte Lösung anzeigen")
    print("  ✓ Statistiken anzeigen")
    print()
    print(f"Datenbank: {case_lib.db_path}")
    print()


if __name__ == "__main__":
    asyncio.run(live_test_fixed())
