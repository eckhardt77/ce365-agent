#!/usr/bin/env python3
"""
Live-Test für Learning System mit echtem Bot

Testet:
1. Erstes Problem → Wird gespeichert
2. Gleiches Problem → Wird erkannt!
3. Stats anzeigen
"""

import asyncio
from techcare.core.bot import TechCareBot
from techcare.learning.case_library import CaseLibrary, Case

async def live_test():
    """Live-Test mit echtem TechCare Bot"""

    print("\n" + "="*80)
    print("  LEARNING SYSTEM - LIVE TEST")
    print("="*80 + "\n")

    # Zuerst: Test-Cases in Datenbank vorbereiten
    print("VORBEREITUNG: Test-Cases in Datenbank laden...")
    print("-" * 80)

    case_lib = CaseLibrary()

    # Test Case 1: Windows Update (für Demo)
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
        print(f"  Bereits {test_case.reuse_count}x wiederverwendet")
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
    print("Ich simuliere jetzt einen User, der ein Windows Update Problem hat.")
    print("TechCare sollte das bekannte Problem erkennen!")
    print()
    input("Drücke ENTER um zu starten...")
    print()

    # Bot initialisieren
    bot = TechCareBot()

    print("\n" + "="*80)
    print("  SIMULATION: User meldet Windows Update Problem")
    print("="*80 + "\n")

    # Erste Message: Neuer Fall
    print("[SIMULATION] User: Neuer Fall")
    print()
    await bot.process_message("Neuer Fall")
    print()

    input("\nDrücke ENTER für User-Antwort auf Startfragen...")
    print()

    # Zweite Message: Problem beschreiben (mit Error-Code!)
    user_response = """Ja, Backup vorhanden via Time Machine.
Windows 11 Pro.
Problem: Windows Update Fehler 0x80070002, Update lädt nicht.
Bereits versucht: Neustart, Windows Update Troubleshooter, aber Problem besteht."""

    print(f"[SIMULATION] User: {user_response[:80]}...")
    print()

    # Problem-Info extrahieren (Learning!)
    bot._extract_problem_info(user_response)

    # Jetzt sollte TechCare ähnlichen Fall finden!
    print("🔍 Learning System prüft auf bekannte Probleme...")
    print()

    similar_found = await bot._check_for_similar_cases()

    if similar_found:
        print()
        print("="*80)
        print("  ✅ ERFOLG! Learning System hat bekanntes Problem erkannt!")
        print("="*80)
        print()
        print("TechCare hat eine bekannte Lösung angeboten!")
        print("User könnte jetzt wählen:")
        print("  1 = Bewährte Lösung (schnell)")
        print("  2 = Vollständiger Audit (gründlich)")
        print()
    else:
        print()
        print("="*80)
        print("  ❌ Kein ähnlicher Fall gefunden")
        print("="*80)
        print()
        print("Mögliche Gründe:")
        print("  - Similarity < 60%")
        print("  - Keine passenden Keywords")
        print("  - OS-Mismatch")
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
    print("  ✓ Ähnlichkeitssuche in Case Library")
    print("  ✓ UI: Bekannte Lösung anzeigen")
    print("  ✓ Statistiken anzeigen")
    print()
    print(f"Datenbank: {case_lib.db_path}")
    print(f"Token-Usage: {bot.client.get_token_usage()['total_tokens']} Tokens")
    print()


if __name__ == "__main__":
    asyncio.run(live_test())
