"""
CE365 Agent - Case Library (Learning System)

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Features:
- SQLAlchemy ORM (PostgreSQL + SQLite)
- Remote DB mit Fallback
- Keyword-basierte Suche
- Success Rate Tracking
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import IntegrityError, OperationalError

from ce365.learning.database import (
    get_db_manager,
    CaseModel,
    KeywordModel
)


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
    - Remote PostgreSQL oder lokales SQLite
    - Keyword-basierte Ähnlichkeitssuche
    - Success Rate Tracking
    - Automatischer Fallback
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: Optional, nur für Legacy/Tests (wird ignoriert wenn Remote-DB konfiguriert)
        """
        self.db_manager = get_db_manager()
        self.db_path = db_path or "Remote DB" if self.db_manager.is_remote() else self.db_manager.settings.learning_db_fallback

    def save_case(self, case: Case) -> int:
        """
        Fall speichern

        Args:
            case: Case-Objekt

        Returns:
            Case ID

        Raises:
            IntegrityError: Wenn session_id bereits existiert
        """
        session = self.db_manager.get_session()

        try:
            # Timestamp setzen
            if not case.created_at:
                case.created_at = datetime.now().isoformat()

            # Case Model erstellen
            case_model = CaseModel(
                created_at=case.created_at,
                os_type=case.os_type,
                os_version=case.os_version,
                problem_description=case.problem_description,
                error_codes=case.error_codes,
                symptoms=case.symptoms,
                root_cause=case.root_cause,
                diagnosis_confidence=case.diagnosis_confidence,
                audit_data=case.audit_data,
                solution_plan=case.solution_plan,
                executed_steps=case.executed_steps,
                success=case.success,
                session_id=case.session_id,
                tokens_used=case.tokens_used,
                duration_minutes=case.duration_minutes,
                reuse_count=case.reuse_count,
                success_rate=case.success_rate
            )

            session.add(case_model)
            session.flush()  # ID generieren

            # Keywords extrahieren und speichern
            keywords = self._extract_keywords(case.problem_description)
            if case.error_codes:
                keywords.extend(self._extract_keywords(case.error_codes))

            # Deduplizierung
            keywords = list(set(keywords))

            for keyword in keywords:
                keyword_model = KeywordModel(
                    case_id=case_model.id,
                    keyword=keyword
                )
                session.add(keyword_model)

            session.commit()

            return case_model.id

        except IntegrityError:
            session.rollback()
            raise

        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Fehler beim Speichern: {e}")

        finally:
            session.close()

    def find_similar_cases(
        self,
        os_type: str,
        problem_description: str,
        error_code: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> List[Tuple[Case, float]]:
        """
        Ähnliche Fälle finden

        Matching-Algorithmus:
        1. Keyword-basierter Match
        2. Error-Code Bonus (+0.5)
        3. Filter nach min_similarity
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
        session = self.db_manager.get_session()

        try:
            # Keywords aus Problem extrahieren
            keywords = self._extract_keywords(problem_description)
            if not keywords:
                return []

            # Query: Cases mit matching Keywords
            query = (
                session.query(
                    CaseModel,
                    func.count(KeywordModel.keyword.distinct()).label('keyword_matches')
                )
                .outerjoin(KeywordModel, CaseModel.id == KeywordModel.case_id)
                .filter(
                    CaseModel.os_type == os_type,
                    CaseModel.success == True
                )
            )

            # Keyword Filter
            if keywords:
                query = query.filter(KeywordModel.keyword.in_(keywords))

            # Group by Case
            query = query.group_by(CaseModel.id)

            # Having: mindestens 1 Keyword Match
            query = query.having(func.count(KeywordModel.keyword.distinct()) > 0)

            # Order by Keyword Matches
            query = query.order_by(
                func.count(KeywordModel.keyword.distinct()).desc(),
                CaseModel.success_rate.desc(),
                CaseModel.reuse_count.desc()
            )

            # Limit * 2 (filtern später nach Similarity)
            query = query.limit(limit * 2)

            results = query.all()

            # Similarity berechnen
            scored_results = []
            total_keywords = len(keywords)

            for case_model, keyword_matches in results:
                # Keyword Similarity
                keyword_similarity = keyword_matches / total_keywords

                # Error-Code Bonus
                error_bonus = 0.0
                if error_code and case_model.error_codes:
                    if error_code.lower() in case_model.error_codes.lower():
                        error_bonus = 0.5

                # Total Similarity
                similarity = min(1.0, keyword_similarity + error_bonus)

                # Filter nach min_similarity
                if similarity >= min_similarity:
                    case = self._model_to_case(case_model)
                    scored_results.append((case, similarity))

            # Nach Similarity sortieren
            scored_results.sort(key=lambda x: x[1], reverse=True)

            return scored_results[:limit]

        except Exception as e:
            print(f"⚠️  Fehler bei Similarity-Suche: {e}")
            return []

        finally:
            session.close()

    def mark_case_reused(self, case_id: int, success: bool):
        """
        Fall als wiederverwendet markieren

        Args:
            case_id: Case ID
            success: War Wiederverwendung erfolgreich?
        """
        session = self.db_manager.get_session()

        try:
            case = session.query(CaseModel).filter(CaseModel.id == case_id).first()

            if not case:
                raise ValueError(f"Case {case_id} nicht gefunden")

            # Reuse Counter erhöhen
            case.reuse_count += 1

            # Success Rate aktualisieren
            total_uses = case.reuse_count + 1  # Original + Reuses
            if success:
                successful_uses = int(case.success_rate * (total_uses - 1)) + 1
            else:
                successful_uses = int(case.success_rate * (total_uses - 1))

            case.success_rate = successful_uses / total_uses

            session.commit()

        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Fehler beim Markieren: {e}")

        finally:
            session.close()

    def get_case_by_id(self, case_id: int) -> Optional[Case]:
        """Fall nach ID holen"""
        session = self.db_manager.get_session()

        try:
            case_model = session.query(CaseModel).filter(CaseModel.id == case_id).first()

            if not case_model:
                return None

            return self._model_to_case(case_model)

        finally:
            session.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Learning-Statistiken holen"""
        session = self.db_manager.get_session()

        try:
            stats = {}

            # Total Cases
            stats['total_cases'] = session.query(CaseModel).count()

            # Erfolgreiche Cases
            stats['successful_cases'] = session.query(CaseModel).filter(CaseModel.success == True).count()

            # Total Reuses
            result = session.query(func.sum(CaseModel.reuse_count)).scalar()
            stats['total_reuses'] = result if result else 0

            # Durchschnittliche Success Rate
            result = session.query(func.avg(CaseModel.success_rate)).scalar()
            stats['avg_success_rate'] = result if result else 0.0

            # OS-Verteilung
            os_dist = session.query(
                CaseModel.os_type,
                func.count(CaseModel.id)
            ).group_by(CaseModel.os_type).all()

            stats['os_distribution'] = {os_type: count for os_type, count in os_dist}

            # Top 5 Lösungen
            top_cases = session.query(CaseModel).filter(
                CaseModel.reuse_count > 0
            ).order_by(
                CaseModel.reuse_count.desc()
            ).limit(5).all()

            stats['top_solutions'] = [
                {
                    'id': case.id,
                    'problem': case.problem_description[:80],
                    'reuse_count': case.reuse_count,
                    'success_rate': case.success_rate
                }
                for case in top_cases
            ]

            return stats

        finally:
            session.close()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Keywords aus Text extrahieren

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

    def _model_to_case(self, model: CaseModel) -> Case:
        """SQLAlchemy Model zu Case Dataclass konvertieren"""
        return Case(
            id=model.id,
            created_at=model.created_at,
            os_type=model.os_type,
            os_version=model.os_version,
            problem_description=model.problem_description,
            error_codes=model.error_codes,
            symptoms=model.symptoms,
            root_cause=model.root_cause,
            diagnosis_confidence=model.diagnosis_confidence,
            audit_data=model.audit_data,
            solution_plan=model.solution_plan,
            executed_steps=model.executed_steps,
            success=model.success,
            session_id=model.session_id,
            tokens_used=model.tokens_used,
            duration_minutes=model.duration_minutes,
            reuse_count=model.reuse_count,
            success_rate=model.success_rate
        )
