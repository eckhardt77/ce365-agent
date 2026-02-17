"""
TechCare Bot - Translation System

Unterstützt Deutsch (de) und Englisch (en)
"""

import json
from pathlib import Path
from typing import Optional


class Translator:
    """Multi-Language Support für TechCare Bot"""

    def __init__(self, language: str = "de"):
        self.language = language
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        """Lädt Übersetzungen aus JSON-Dateien"""
        lang_dir = Path(__file__).parent / "languages"
        lang_file = lang_dir / f"{self.language}.json"

        if not lang_file.exists():
            # Fallback auf Deutsch
            lang_file = lang_dir / "de.json"
            self.language = "de"

        with open(lang_file, 'r', encoding='utf-8') as f:
            self.translations = json.load(f)

    def t(self, key: str, **kwargs) -> str:
        """
        Übersetzt einen Key

        Args:
            key: Translation Key (z.B. "errors.api_key_missing")
            **kwargs: Variablen für Formatierung (z.B. {count}, {name})

        Returns:
            Übersetzter Text

        Example:
            t("system.welcome", name="Carsten")
            → "Willkommen, Carsten!"
        """
        # Nested Key Support (z.B. "errors.api_key_missing")
        keys = key.split('.')
        value = self.translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Fallback: Key selbst zurückgeben
                return f"[MISSING: {key}]"

        # String-Formatierung
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return value

    def change_language(self, language: str) -> bool:
        """
        Ändert die Sprache zur Laufzeit

        Args:
            language: "de" oder "en"

        Returns:
            True wenn erfolgreich
        """
        if language not in ["de", "en"]:
            return False

        self.language = language
        self.load_translations()
        return True

    def get_available_languages(self) -> dict:
        """Gibt verfügbare Sprachen zurück"""
        return {
            "de": "Deutsch",
            "en": "English"
        }


# Globale Translator-Instanz
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Singleton Pattern für Translator"""
    global _translator
    if _translator is None:
        # Sprache aus Config laden
        from techcare.config.settings import get_settings
        settings = get_settings()
        language = getattr(settings, 'language', 'de')
        _translator = Translator(language=language)
    return _translator


def set_language(language: str) -> bool:
    """
    Ändert die globale Sprache

    Args:
        language: "de" oder "en"

    Returns:
        True wenn erfolgreich
    """
    translator = get_translator()
    success = translator.change_language(language)

    if success:
        # In Config speichern
        from techcare.config.settings import get_settings
        settings = get_settings()
        settings.language = language
        settings.save()

    return success
