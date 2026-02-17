"""
Case Library für TechCare Bot

Speichert und verwaltet gelöste Fälle für Learning System
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from techcare.config.settings import get_settings


@dataclass
class Case:
    """Gespeicherter Fall"""

    # Problem
    os_type: str  # 'windows' oder 'macos'
    os_version: str
    problem_description: str
    error_codes: Optional[str] = None
    symptoms: Optional[str] = None  # JSON

    # Diagnose
    root_cause: str = ""
    diagnosis_confidence: float = 1.0
    audit_data: Optional[str] = None  # JSON

    # Lösung
    solution_plan: str = ""
    executed_steps: str = ""  # JSON
    success: bool = False

    # Meta
    session_id: str = ""
    tokens_used: int = 0
    duration_minutes: int = 0

    # Learning
    reuse_count: int = 0
    success_rate: float = 0.0

    # ID (wird von DB gesetzt)
    id: Optional[int] = None
    created_at: Optional[str] = None


class CaseLibrary:
    """
    Case Library für gespeicherte Fälle

    Features:
    - Speichern erfolgreicher Lösungen
    - Suchen ähnlicher Fälle (Keyword-basiert)
    - Success Rate Tracking
    - Wiederverwendungs-Counter
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            settings = get_settings()
            db_path = str(settings.data_dir / "cases.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Datenbank initialisieren"""
        # Sicherstellen, dass Verzeichnis existiert
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cases Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Problem
                os_type TEXT NOT NULL,
                os_version TEXT,
                problem_description TEXT NOT NULL,
                error_codes TEXT,
                symptoms TEXT,

                -- Diagnose
                root_cause TEXT NOT NULL,
                diagnosis_confidence REAL DEFAULT 1.0,
                audit_data TEXT,

                -- Lösung
                solution_plan TEXT NOT NULL,
                executed_steps TEXT,
                success BOOLEAN DEFAULT FALSE,

                -- Meta
                session_id TEXT UNIQUE,
                tokens_used INTEGER DEFAULT 0,
                duration_minutes INTEGER DEFAULT 0,

                -- Learning
                reuse_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            )
        """)

        # Keywords Tabelle (für schnelle Suche)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """)

        # Indices für Performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_os_type ON cases(os_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_codes ON cases(error_codes)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_success ON cases(success)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON case_keywords(keyword)")

        conn.commit()
        conn.close()

    def save_case(self, case: Case) -> int:
        """
        Fall speichern

        Args:
            case: Case-Objekt

        Returns:
            case_id: ID des gespeicherten Falls
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO cases (
                    os_type, os_version, problem_description, error_codes, symptoms,
                    root_cause, diagnosis_confidence, audit_data,
                    solution_plan, executed_steps, success,
                    session_id, tokens_used, duration_minutes,
                    reuse_count, success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case.os_type, case.os_version, case.problem_description,
                case.error_codes, case.symptoms,
                case.root_cause, case.diagnosis_confidence, case.audit_data,
                case.solution_plan, case.executed_steps, case.success,
                case.session_id, case.tokens_used, case.duration_minutes,
                case.reuse_count, case.success_rate
            ))

            case_id = cursor.lastrowid

            # Keywords extrahieren und speichern
            keywords = self._extract_keywords(case.problem_description)
            if case.error_codes:
                keywords.extend(self._extract_keywords(case.error_codes))

            for keyword in set(keywords):  # Deduplizieren
                cursor.execute("""
                    INSERT INTO case_keywords (case_id, keyword)
                    VALUES (?, ?)
                """, (case_id, keyword))

            conn.commit()
            return case_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Fehler beim Speichern des Falls: {str(e)}")
        finally:
            conn.close()

    def find_similar_cases(
        self,
        os_type: str,
        problem_description: str,
        error_code: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> List[tuple[Case, float]]:
        """
        Ähnliche Fälle finden

        Matching-Kriterien:
        1. OS-Type Match (Pflicht)
        2. Error-Code Match (wenn vorhanden, stark gewichtet)
        3. Keyword-Overlap (Gewichtet nach Anzahl)
        4. Nur erfolgreiche Fälle

        Args:
            os_type: Betriebssystem
            problem_description: Problem-Beschreibung
            error_code: Optional Error-Code
            limit: Max Anzahl Ergebnisse
            min_similarity: Mindest-Ähnlichkeit (0.0-1.0)

        Returns:
            List[(Case, similarity_score)]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Keywords aus Problem extrahieren
        keywords = self._extract_keywords(problem_description)
        if not keywords:
            conn.close()
            return []

        # Query aufbauen
        query = """
            SELECT DISTINCT
                c.*,
                COUNT(DISTINCT k.keyword) as keyword_matches,
                CASE
                    WHEN c.error_codes LIKE ? THEN 10.0
                    ELSE 0.0
                END as error_code_bonus
            FROM cases c
            LEFT JOIN case_keywords k ON c.id = k.case_id
            WHERE c.os_type = ?
              AND c.success = 1
        """

        params = []

        # Error-Code Parameter (für CASE)
        if error_code:
            params.append(f"%{error_code}%")
        else:
            params.append("%NOERRORCODE%")  # Dummy

        params.append(os_type)

        # Keyword Filter
        if keywords:
            placeholders = ",".join("?" * len(keywords))
            query += f" AND k.keyword IN ({placeholders})"
            params.extend(keywords)

        query += """
            GROUP BY c.id
            HAVING keyword_matches > 0
            ORDER BY
                (keyword_matches + error_code_bonus) DESC,
                c.success_rate DESC,
                c.reuse_count DESC
            LIMIT ?
        """
        params.append(limit * 2)  # Holen mehr, filtern später

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        # Cases erstellen und Similarity berechnen
        results = []
        total_keywords = len(keywords)

        for row in rows:
            case = self._row_to_case(row)
            keyword_matches = row[18]  # keyword_matches column
            error_code_bonus = row[19]  # error_code_bonus column

            # Similarity Score berechnen
            # - Keyword-Match: 0-1 (Anteil übereinstimmender Keywords)
            # - Error-Code-Match: +0.5 Bonus
            keyword_similarity = keyword_matches / total_keywords
            error_bonus = 0.5 if error_code_bonus > 0 else 0.0

            similarity = min(1.0, keyword_similarity + error_bonus)

            # Filter: Mindest-Ähnlichkeit
            if similarity >= min_similarity:
                results.append((case, similarity))

        # Nach Similarity sortieren
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:limit]

    def get_case_by_id(self, case_id: int) -> Optional[Case]:
        """Fall nach ID holen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._row_to_case(row)
        return None

    def mark_case_reused(self, case_id: int, success: bool):
        """
        Fall als wiederverwendet markieren

        Aktualisiert:
        - reuse_count (+1)
        - success_rate (neu berechnet)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Aktuellen Stand holen
            cursor.execute("""
                SELECT reuse_count, success_rate
                FROM cases
                WHERE id = ?
            """, (case_id,))

            row = cursor.fetchone()
            if not row:
                return

            reuse_count, success_rate = row

            # Neue Success Rate berechnen
            # (alte_rate * alte_count + neue_bewertung) / neue_count
            new_reuse_count = reuse_count + 1
            new_success = 1.0 if success else 0.0
            new_success_rate = (success_rate * reuse_count + new_success) / new_reuse_count

            # Update
            cursor.execute("""
                UPDATE cases
                SET reuse_count = ?,
                    success_rate = ?
                WHERE id = ?
            """, (new_reuse_count, new_success_rate, case_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Fehler beim Aktualisieren des Falls: {str(e)}")
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Statistiken über gespeicherte Fälle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Gesamte Fälle
        cursor.execute("SELECT COUNT(*) FROM cases")
        stats['total_cases'] = cursor.fetchone()[0]

        # Erfolgreiche Fälle
        cursor.execute("SELECT COUNT(*) FROM cases WHERE success = 1")
        stats['successful_cases'] = cursor.fetchone()[0]

        # Wiederverwendungen
        cursor.execute("SELECT SUM(reuse_count) FROM cases")
        stats['total_reuses'] = cursor.fetchone()[0] or 0

        # Durchschnittliche Success Rate
        cursor.execute("SELECT AVG(success_rate) FROM cases WHERE reuse_count > 0")
        avg_rate = cursor.fetchone()[0]
        stats['avg_success_rate'] = avg_rate if avg_rate else 0.0

        # OS-Verteilung
        cursor.execute("""
            SELECT os_type, COUNT(*) as count
            FROM cases
            GROUP BY os_type
        """)
        stats['os_distribution'] = dict(cursor.fetchall())

        # Top 5 Lösungen
        cursor.execute("""
            SELECT id, problem_description, reuse_count, success_rate
            FROM cases
            WHERE reuse_count > 0
            ORDER BY reuse_count DESC
            LIMIT 5
        """)
        stats['top_solutions'] = [
            {
                'id': row[0],
                'problem': row[1][:80],
                'reuse_count': row[2],
                'success_rate': row[3]
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        return stats

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Keywords aus Text extrahieren

        Einfache Version:
        - Lowercase
        - Min 3 Zeichen
        - Keine Stopwords
        - Zahlen erlaubt (für Error-Codes)
        """
        stopwords = {
            'der', 'die', 'das', 'und', 'ist', 'nicht', 'ein', 'eine',
            'mit', 'für', 'auf', 'von', 'zu', 'bei', 'nach', 'vor',
            'ich', 'mein', 'habe', 'kann', 'wird', 'wurde', 'aber',
            'auch', 'aus', 'dem', 'den', 'des', 'sich', 'sind', 'war',
            'werden', 'wie', 'zum', 'zur', 'haben', 'hatte', 'wenn',
            'dann', 'noch', 'nur', 'oder', 'als', 'bis', 'beim'
        }

        # Text bereinigen
        import re
        text = text.lower()
        # Behalte Buchstaben, Zahlen und Bindestriche
        text = re.sub(r'[^a-zäöüß0-9\s-]', ' ', text)

        words = text.split()
        keywords = [
            w for w in words
            if len(w) >= 3 and w not in stopwords
        ]

        return keywords

    def _row_to_case(self, row: tuple) -> Case:
        """Datenbank-Row zu Case-Objekt konvertieren"""
        return Case(
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

    def __repr__(self):
        stats = self.get_statistics()
        return (
            f"CaseLibrary("
            f"cases={stats['total_cases']}, "
            f"successful={stats['successful_cases']}, "
            f"reuses={stats['total_reuses']})"
        )
