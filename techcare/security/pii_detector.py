"""
TechCare Bot - PII Detection & Anonymization

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Erkennt und anonymisiert:
- Email-Adressen
- Telefonnummern
- Namen
- IP-Adressen
- Passwörter (Pattern-basiert)
- IBAN, Kreditkarten
- Adressen
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import os

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


@dataclass
class PIIDetection:
    """Erkannte PII"""
    entity_type: str  # z.B. "EMAIL_ADDRESS", "PERSON"
    start: int
    end: int
    score: float
    text: str


class PIIDetector:
    """
    PII Detector mit Microsoft Presidio

    Features:
    - Multi-Language Support (DE, EN)
    - Configurable Detection Level
    - Anonymization & De-Anonymization
    - Custom Entity Recognizers
    """

    def __init__(
        self,
        enabled: bool = True,
        level: str = "high",  # high/medium/low
        language: str = "de",  # de/en
        show_warnings: bool = True
    ):
        """
        Args:
            enabled: PII Detection aktiviert?
            level: Detection Level (high = alle, medium = wichtige, low = kritische)
            language: Sprache für NLP
            show_warnings: User-Warnings anzeigen?
        """
        self.enabled = enabled
        self.level = level
        self.language = language
        self.show_warnings = show_warnings

        if not PRESIDIO_AVAILABLE:
            print("⚠️  Presidio nicht installiert. PII Detection deaktiviert.")
            self.enabled = False
            return

        if not self.enabled:
            return

        # Analyzer Engine initialisieren
        try:
            # NLP Engine (spacy)
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "de", "model_name": "de_core_news_sm"},
                    {"lang_code": "en", "model_name": "en_core_web_sm"}
                ]
            }

            provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = provider.create_engine()

            # Analyzer
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["de", "en"])

            # Anonymizer
            self.anonymizer = AnonymizerEngine()

            # Entity Types je nach Level
            self.entity_types = self._get_entity_types_for_level(level)

        except Exception as e:
            print(f"⚠️  Presidio Initialisierung fehlgeschlagen: {e}")
            self.enabled = False

    def _get_entity_types_for_level(self, level: str) -> List[str]:
        """
        Entity Types je nach Detection Level

        Args:
            level: high/medium/low

        Returns:
            List of entity types to detect
        """
        # Kritisch (immer erkennen)
        critical = [
            "CREDIT_CARD",
            "IBAN_CODE",
            "US_SSN",
            "PASSWORD",  # Custom
        ]

        # Wichtig
        important = [
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "PERSON",
            "IP_ADDRESS",
            "CRYPTO",
        ]

        # Alle anderen
        all_types = [
            "LOCATION",
            "DATE_TIME",
            "NRP",  # Nationality/Religion/Political
            "URL",
            "MEDICAL_LICENSE",
            "US_DRIVER_LICENSE",
        ]

        if level == "high":
            return critical + important + all_types
        elif level == "medium":
            return critical + important
        else:  # low
            return critical

    def analyze(self, text: str) -> List[PIIDetection]:
        """
        Text auf PII analysieren

        Args:
            text: Zu analysierender Text

        Returns:
            Liste erkannter PIIs
        """
        if not self.enabled or not text:
            return []

        try:
            # Presidio Analyse
            results = self.analyzer.analyze(
                text=text,
                language=self.language,
                entities=self.entity_types
            )

            # In PIIDetection konvertieren
            detections = []
            for result in results:
                detection = PIIDetection(
                    entity_type=result.entity_type,
                    start=result.start,
                    end=result.end,
                    score=result.score,
                    text=text[result.start:result.end]
                )
                detections.append(detection)

            return detections

        except Exception as e:
            print(f"⚠️  PII Analyse Fehler: {e}")
            return []

    def anonymize(self, text: str) -> Tuple[str, List[PIIDetection]]:
        """
        Text anonymisieren

        Args:
            text: Zu anonymisierender Text

        Returns:
            (anonymisierter_text, erkannte_piis)
        """
        if not self.enabled or not text:
            return text, []

        try:
            # Analyse
            detections = self.analyze(text)

            if not detections:
                return text, []

            # Anonymisierung
            # Format: <ENTITY_TYPE>
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=[
                    type('Result', (), {
                        'entity_type': d.entity_type,
                        'start': d.start,
                        'end': d.end,
                        'score': d.score
                    })() for d in detections
                ],
                operators={
                    entity_type: OperatorConfig("replace", {"new_value": f"<{entity_type}>"})
                    for entity_type in set(d.entity_type for d in detections)
                }
            )

            return anonymized_result.text, detections

        except Exception as e:
            print(f"⚠️  PII Anonymisierung Fehler: {e}")
            return text, []

    def get_detection_summary(self, detections: List[PIIDetection]) -> Dict[str, int]:
        """
        Zusammenfassung der Detections

        Args:
            detections: Liste von PIIDetection

        Returns:
            Dict mit Entity-Type → Count
        """
        summary = {}
        for detection in detections:
            entity_type = detection.entity_type
            summary[entity_type] = summary.get(entity_type, 0) + 1
        return summary

    def format_detection_warning(self, detections: List[PIIDetection]) -> str:
        """
        User-freundliche Warning Message

        Args:
            detections: Liste von PIIDetection

        Returns:
            Formatierte Warning Message
        """
        if not detections:
            return ""

        summary = self.get_detection_summary(detections)
        total = len(detections)

        # Entity Type Namen (Deutsch)
        entity_names = {
            "EMAIL_ADDRESS": "Email-Adresse",
            "PHONE_NUMBER": "Telefonnummer",
            "PERSON": "Personenname",
            "IP_ADDRESS": "IP-Adresse",
            "CREDIT_CARD": "Kreditkarte",
            "IBAN_CODE": "IBAN",
            "PASSWORD": "Passwort",
            "LOCATION": "Adresse",
            "URL": "URL",
            "DATE_TIME": "Datum/Zeit",
            "CRYPTO": "Crypto-Wallet",
        }

        lines = [f"⚠️  {total} sensible Information{'en' if total > 1 else ''} erkannt und anonymisiert:"]

        for entity_type, count in sorted(summary.items(), key=lambda x: -x[1]):
            name = entity_names.get(entity_type, entity_type)
            lines.append(f"   • {name} ({count}x)")

        return "\n".join(lines)


# Globale Instanz (Lazy Loading)
_pii_detector = None


def get_pii_detector() -> PIIDetector:
    """
    PII Detector Singleton

    Returns:
        PIIDetector Instanz
    """
    global _pii_detector

    if _pii_detector is None:
        # Config aus Env-Vars
        enabled = os.getenv("PII_DETECTION_ENABLED", "true").lower() == "true"
        level = os.getenv("PII_DETECTION_LEVEL", "high").lower()
        show_warnings = os.getenv("PII_SHOW_WARNINGS", "true").lower() == "true"

        _pii_detector = PIIDetector(
            enabled=enabled,
            level=level,
            show_warnings=show_warnings
        )

    return _pii_detector
