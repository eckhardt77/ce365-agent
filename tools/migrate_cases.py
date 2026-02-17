#!/usr/bin/env python3
"""
Case Migration Script

Migriert Cases von:
- SQLite → PostgreSQL
- SQLite → SQLite (Backup/Restore)

Usage:
    python tools/migrate_cases.py --source data/cases.db --target postgresql
    python tools/migrate_cases.py --export data/cases_backup.db
"""

import argparse
import sys
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ce365.learning.case_library import CaseLibrary, Case
from ce365.learning.database import get_db_manager, CaseModel, KeywordModel
from ce365.config.settings import get_settings


def migrate_sqlite_to_remote(source_db: str):
    """
    SQLite Cases zu Remote-DB migrieren

    Args:
        source_db: Pfad zur Quell-SQLite-DB
    """
    print("\n" + "="*80)
    print("  CASE MIGRATION: SQLite → Remote DB")
    print("="*80 + "\n")

    # Source: SQLite direkt öffnen
    if not Path(source_db).exists():
        print(f"❌ Quell-Datenbank nicht gefunden: {source_db}")
        return

    print(f"📂 Quell-DB: {source_db}")

    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()

    # Cases zählen
    cursor.execute("SELECT COUNT(*) FROM cases")
    total_cases = cursor.fetchone()[0]

    print(f"📊 {total_cases} Cases in Quell-DB gefunden")
    print()

    # Target: Remote DB (via CaseLibrary)
    target_lib = CaseLibrary()
    db_manager = get_db_manager()

    if not db_manager.is_remote():
        print("⚠️  Warnung: Ziel ist auch SQLite (kein Remote-Server konfiguriert)")
        print(f"   Ziel-DB: {db_manager.settings.learning_db_fallback}")
        print()
        response = input("Trotzdem fortfahren? (y/n): ")
        if response.lower() != 'y':
            print("Migration abgebrochen.")
            return
    else:
        print(f"✓ Remote-DB verbunden")
        print()

    # Migration starten
    print("🔄 Migration starten...")
    print("-" * 80)

    cursor.execute("SELECT * FROM cases")
    cases = cursor.fetchall()

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for row in cases:
        try:
            # Case-Objekt erstellen
            case = Case(
                id=row[0],
                created_at=row[1],
                os_type=row[2],
                os_version=row[3],
                problem_description=row[4],
                error_codes=row[5],
                symptoms=row[6],
                root_cause=row[7],
                diagnosis_confidence=row[8],
                audit_data=row[9],
                solution_plan=row[10],
                executed_steps=row[11],
                success=bool(row[12]),
                session_id=row[13],
                tokens_used=row[14],
                duration_minutes=row[15],
                reuse_count=row[16],
                success_rate=row[17]
            )

            # In Ziel-DB speichern
            target_lib.save_case(case)
            migrated_count += 1
            print(f"  ✓ Case {case.id}: {case.problem_description[:60]}...")

        except Exception as e:
            if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
                skipped_count += 1
                print(f"  ⊘ Case {row[0]}: Bereits vorhanden (übersprungen)")
            else:
                error_count += 1
                print(f"  ✗ Case {row[0]}: Fehler - {str(e)[:60]}")

    conn.close()

    # Zusammenfassung
    print()
    print("="*80)
    print("  MIGRATION ABGESCHLOSSEN")
    print("="*80)
    print()
    print(f"📊 Statistik:")
    print(f"  ✓ Migriert: {migrated_count}")
    print(f"  ⊘ Übersprungen: {skipped_count}")
    print(f"  ✗ Fehler: {error_count}")
    print(f"  ━ Gesamt: {total_cases}")
    print()


def export_cases_to_json(source_db: str, output_file: str = "cases_export.json"):
    """
    Cases zu JSON exportieren (für Backup/Sharing)

    Args:
        source_db: Pfad zur Quell-DB
        output_file: Ziel-JSON-Datei
    """
    import json

    print("\n" + "="*80)
    print("  CASE EXPORT: DB → JSON")
    print("="*80 + "\n")

    if not Path(source_db).exists():
        print(f"❌ Datenbank nicht gefunden: {source_db}")
        return

    print(f"📂 Quell-DB: {source_db}")

    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()

    # Cases laden
    cursor.execute("SELECT * FROM cases")
    cases = cursor.fetchall()

    print(f"📊 {len(cases)} Cases gefunden")
    print()

    # Als JSON exportieren
    cases_data = []

    for row in cases:
        case_dict = {
            'id': row[0],
            'created_at': row[1],
            'os_type': row[2],
            'os_version': row[3],
            'problem_description': row[4],
            'error_codes': row[5],
            'symptoms': row[6],
            'root_cause': row[7],
            'diagnosis_confidence': row[8],
            'audit_data': row[9],
            'solution_plan': row[10],
            'executed_steps': row[11],
            'success': bool(row[12]),
            'session_id': row[13],
            'tokens_used': row[14],
            'duration_minutes': row[15],
            'reuse_count': row[16],
            'success_rate': row[17]
        }
        cases_data.append(case_dict)

    # JSON schreiben
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cases_data, f, indent=2, ensure_ascii=False)

    conn.close()

    print(f"✓ Export erfolgreich: {output_file}")
    print(f"  {len(cases_data)} Cases exportiert")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="CE365 Case Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:

  # SQLite → Remote PostgreSQL migrieren
  python tools/migrate_cases.py --source data/cases.db --target remote

  # Cases zu JSON exportieren
  python tools/migrate_cases.py --source data/cases.db --export cases_backup.json

  # JSON importieren (TODO)
  python tools/migrate_cases.py --import cases_backup.json
        """
    )

    parser.add_argument('--source', '-s', help='Quell-Datenbank (SQLite)')
    parser.add_argument('--target', '-t', choices=['remote', 'local'], help='Ziel: remote (PostgreSQL) oder local (SQLite)')
    parser.add_argument('--export', '-e', nargs='?', const='cases_export.json', help='Cases zu JSON exportieren')
    parser.add_argument('--import', '-i', dest='import_file', help='Cases von JSON importieren (TODO)')

    args = parser.parse_args()

    if args.export:
        if not args.source:
            print("❌ --source erforderlich für Export")
            sys.exit(1)
        export_cases_to_json(args.source, args.export)

    elif args.target == 'remote':
        if not args.source:
            print("❌ --source erforderlich für Migration")
            sys.exit(1)
        migrate_sqlite_to_remote(args.source)

    elif args.import_file:
        print("❌ Import von JSON noch nicht implementiert")
        sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
