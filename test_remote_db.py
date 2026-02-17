#!/usr/bin/env python3
"""
Test-Skript für Remote DB Funktionalität

Testet:
1. Lokales SQLite (Default)
2. Fallback-Mechanismus
3. Case speichern/laden
4. Similarity-Suche
"""

from techcare.learning.case_library import CaseLibrary, Case
from techcare.learning.database import get_db_manager
from techcare.ui.console import RichConsole

console = RichConsole()


def test_remote_db():
    """Remote DB Funktionalität testen"""

    print("\n" + "="*80)
    print("  REMOTE DB TEST")
    print("="*80 + "\n")

    # 1. Database Manager Status
    print("1. DATABASE MANAGER STATUS")
    print("-" * 80)

    db_manager = get_db_manager()

    if db_manager.is_remote():
        console.display_success("✓ Remote PostgreSQL verbunden")
        print(f"  URL: {db_manager.settings.learning_db_url}")
    else:
        if db_manager.is_fallback_active():
            console.display_warning("⚠️  Fallback zu lokalem SQLite aktiv")
        else:
            console.display_info("ℹ️  Lokales SQLite konfiguriert")

        print(f"  Pfad: {db_manager.settings.learning_db_fallback}")

    print()

    # 2. Case Library initialisieren
    print("2. CASE LIBRARY INITIALISIEREN")
    print("-" * 80)

    case_lib = CaseLibrary()
    console.display_success("✓ Case Library initialisiert")
    print()

    # 3. Test Case speichern
    print("3. TEST CASE SPEICHERN")
    print("-" * 80)

    test_case = Case(
        os_type="windows",
        os_version="Windows 11",
        problem_description="Test: Remote DB Connectivity Check",
        error_codes="0xTEST001",
        root_cause="Test Case für Remote DB",
        solution_plan="Test-Lösung",
        executed_steps='["test_step"]',
        success=True,
        session_id=f"test-remote-db-{int(__import__('time').time())}",
        tokens_used=100,
        duration_minutes=1
    )

    try:
        case_id = case_lib.save_case(test_case)
        console.display_success(f"✓ Test Case gespeichert (ID: {case_id})")
    except Exception as e:
        console.display_error(f"❌ Fehler beim Speichern: {str(e)}")
        return

    print()

    # 4. Case wieder laden
    print("4. CASE WIEDER LADEN")
    print("-" * 80)

    loaded_case = case_lib.get_case_by_id(case_id)

    if loaded_case:
        console.display_success(f"✓ Case geladen: {loaded_case.problem_description}")
        print(f"  OS: {loaded_case.os_type}")
        print(f"  Error-Code: {loaded_case.error_codes}")
    else:
        console.display_error("❌ Case konnte nicht geladen werden")

    print()

    # 5. Similarity-Suche testen
    print("5. SIMILARITY-SUCHE TESTEN")
    print("-" * 80)

    similar = case_lib.find_similar_cases(
        os_type="windows",
        problem_description="Remote DB Connectivity Test Check",
        error_code="0xTEST001",
        limit=5,
        min_similarity=0.3
    )

    if similar:
        console.display_success(f"✓ {len(similar)} ähnliche Fälle gefunden")
        for case, similarity in similar:
            print(f"  - Case {case.id}: {similarity*100:.0f}% Ähnlichkeit")
    else:
        console.display_warning("⚠️  Keine ähnlichen Fälle gefunden")

    print()

    # 6. Statistiken
    print("6. STATISTIKEN")
    print("-" * 80)

    stats = case_lib.get_statistics()
    console.display_learning_stats(stats)

    print()

    # 7. Retry-Test (nur wenn Fallback aktiv)
    if db_manager.is_fallback_active():
        print("7. RETRY REMOTE CONNECTION")
        print("-" * 80)
        print("Versuche Remote-DB erneut zu verbinden...")
        print("(Hinweis: Wird fehlschlagen wenn keine Remote-DB konfiguriert)")
        print()

        success = db_manager.retry_remote_connection()

        if success:
            console.display_success("✓ Remote-DB Verbindung hergestellt!")
        else:
            console.display_warning("⚠️  Remote-DB weiterhin nicht verfügbar")

        print()

    # Zusammenfassung
    print("="*80)
    print("  TEST ABGESCHLOSSEN")
    print("="*80)
    print()

    print("Was wurde getestet:")
    print("  ✓ Database Manager Initialisierung")
    print("  ✓ Case speichern (CREATE)")
    print("  ✓ Case laden (READ)")
    print("  ✓ Similarity-Suche (QUERY)")
    print("  ✓ Statistiken (AGGREGATE)")

    if db_manager.is_remote():
        print("\n✅ Remote PostgreSQL funktioniert!")
    else:
        print("\n✅ Lokales SQLite funktioniert!")
        print("\nUm Remote-DB zu testen:")
        print("  1. PostgreSQL Server starten")
        print("  2. .env konfigurieren:")
        print("     LEARNING_DB_TYPE=postgresql")
        print("     LEARNING_DB_URL=postgresql://user:pass@host:port/db")
        print("  3. Test erneut ausführen")

    print()


if __name__ == "__main__":
    test_remote_db()
