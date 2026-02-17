#!/usr/bin/env python3
"""
Debug-Skript für Learning System

Zeigt Schritt-für-Schritt was bei der Similarity-Suche passiert
"""

import sqlite3
from techcare.learning.case_library import CaseLibrary

def debug_similarity_search():
    """Detailliertes Debugging der Similarity-Suche"""

    print("\n" + "="*80)
    print("  LEARNING SYSTEM DEBUG")
    print("="*80 + "\n")

    case_lib = CaseLibrary()

    # 1. Prüfe was in der DB ist
    print("1. DATENBANK-INHALT")
    print("-" * 80)

    conn = sqlite3.connect(case_lib.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, os_type, problem_description, error_codes FROM cases")
    cases = cursor.fetchall()

    print(f"Anzahl Cases in DB: {len(cases)}\n")

    for case_id, os_type, problem, error_codes in cases:
        print(f"Case ID {case_id}:")
        print(f"  OS: {os_type}")
        print(f"  Problem: {problem[:100]}...")
        print(f"  Error Codes: {error_codes}")

        # Keywords für diesen Case holen
        cursor.execute("SELECT keyword FROM case_keywords WHERE case_id = ?", (case_id,))
        keywords = [row[0] for row in cursor.fetchall()]
        print(f"  Keywords in DB: {keywords}")
        print()

    # 2. User-Input simulieren
    print("\n2. USER-INPUT SIMULIEREN")
    print("-" * 80)

    user_input = """Ja, Backup vorhanden via Time Machine.
Windows 11 Pro.
Problem: Windows Update Fehler 0x80070002, Update lädt nicht.
Bereits versucht: Neustart, Windows Update Troubleshooter, aber Problem besteht."""

    print(f"User-Input:\n{user_input}\n")

    # Keywords extrahieren
    extracted_keywords = case_lib._extract_keywords(user_input)
    print(f"Extrahierte Keywords ({len(extracted_keywords)}):")
    print(f"  {extracted_keywords}\n")

    # 3. Similarity-Suche durchführen
    print("\n3. SIMILARITY-SUCHE")
    print("-" * 80)

    os_type = "windows"
    error_code = "0x80070002"

    print(f"Suche nach:")
    print(f"  OS: {os_type}")
    print(f"  Error-Code: {error_code}")
    print(f"  Keywords: {extracted_keywords}")
    print()

    # Manuell SQL Query nachbauen für Debug
    placeholders = ",".join("?" * len(extracted_keywords))
    query = f"""
        SELECT DISTINCT
            c.id,
            c.problem_description,
            COUNT(DISTINCT k.keyword) as keyword_matches,
            CASE
                WHEN c.error_codes LIKE ? THEN 10.0
                ELSE 0.0
            END as error_code_bonus
        FROM cases c
        LEFT JOIN case_keywords k ON c.id = k.case_id
        WHERE c.os_type = ?
          AND c.success = 1
          AND k.keyword IN ({placeholders})
        GROUP BY c.id
        HAVING keyword_matches > 0
        ORDER BY
            (keyword_matches + error_code_bonus) DESC
    """

    params = [f"%{error_code}%", os_type] + extracted_keywords

    print("SQL Query Parameter:")
    print(f"  Error-Code Pattern: %{error_code}%")
    print(f"  OS Type: {os_type}")
    print(f"  Keywords: {extracted_keywords[:5]}... (first 5)")
    print()

    cursor.execute(query, params)
    results = cursor.fetchall()

    print(f"SQL Query Ergebnisse: {len(results)}\n")

    if results:
        for case_id, problem, keyword_matches, error_bonus in results:
            print(f"Case {case_id}:")
            print(f"  Problem: {problem[:80]}...")
            print(f"  Keyword Matches: {keyword_matches}")
            print(f"  Error-Code Bonus: {error_bonus}")

            # Similarity berechnen
            keyword_similarity = keyword_matches / len(extracted_keywords)
            error_bonus_calc = 0.5 if error_bonus > 0 else 0.0
            similarity = min(1.0, keyword_similarity + error_bonus_calc)

            print(f"  Similarity Berechnung:")
            print(f"    Keyword Similarity: {keyword_matches}/{len(extracted_keywords)} = {keyword_similarity:.2f}")
            print(f"    Error-Code Bonus: {error_bonus_calc}")
            print(f"    Total Similarity: {similarity:.2f} ({similarity*100:.0f}%)")
            print(f"    Min Similarity: 0.60 (60%)")
            print(f"    Match: {'✓ JA' if similarity >= 0.6 else '✗ NEIN'}")
            print()
    else:
        print("❌ Keine Ergebnisse!")
        print()
        print("Mögliche Gründe:")
        print("  1. Keine Keyword-Übereinstimmungen (k.keyword IN (...) findet nichts)")
        print("  2. OS-Type stimmt nicht überein")
        print("  3. success = 1 Filter schließt Cases aus")
        print()

        # Debug: Prüfe Keywords einzeln
        print("Debug: Prüfe Keywords einzeln")
        print("-" * 80)
        for keyword in extracted_keywords[:10]:  # Nur erste 10
            cursor.execute("""
                SELECT DISTINCT c.id, k.keyword
                FROM cases c
                JOIN case_keywords k ON c.id = k.case_id
                WHERE k.keyword = ? AND c.os_type = ?
            """, (keyword, os_type))
            matches = cursor.fetchall()
            if matches:
                print(f"  '{keyword}' → {len(matches)} matches")
        print()

    conn.close()

    # 4. Offizielle API testen
    print("\n4. OFFIZIELLE API TESTEN")
    print("-" * 80)

    similar = case_lib.find_similar_cases(
        os_type=os_type,
        problem_description=user_input,
        error_code=error_code,
        limit=3,
        min_similarity=0.6
    )

    if similar:
        print(f"✓ {len(similar)} ähnliche Fälle gefunden:\n")
        for case, similarity in similar:
            print(f"  Case {case.id}: {similarity*100:.0f}% Ähnlichkeit")
            print(f"  Problem: {case.problem_description[:80]}...")
            print()
    else:
        print("❌ Keine ähnlichen Fälle gefunden (< 60% Similarity)\n")

    print("="*80)
    print("  DEBUG ABGESCHLOSSEN")
    print("="*80)
    print()


if __name__ == "__main__":
    debug_similarity_search()
