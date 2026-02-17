import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# .env laden
load_dotenv()


class Settings(BaseModel):
    """Globale Einstellungen für TechCare Bot"""

    # API
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"

    # Logging
    log_level: str = "INFO"

    # Pfade
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    sessions_dir: Path = data_dir / "sessions"
    changelogs_dir: Path = data_dir / "changelogs"

    # Learning System - Database
    learning_db_type: str = "sqlite"  # "sqlite", "postgresql" oder "mysql"
    learning_db_url: str = ""  # PostgreSQL/MySQL URL (wenn learning_db_type="postgresql" oder "mysql")
    learning_db_fallback: str = "data/cases.db"  # Lokaler Fallback
    learning_db_timeout: int = 5  # Connection Timeout in Sekunden
    learning_db_retry: int = 3  # Anzahl Retry-Versuche

    # Security - PII Detection (Presidio)
    pii_detection_enabled: bool = True  # PII Detection aktivieren
    pii_detection_level: str = "high"  # "high", "medium" oder "low"
    pii_show_warnings: bool = True  # User-Warnings anzeigen

    @classmethod
    def load(cls) -> "Settings":
        """Settings aus Environment-Variablen laden"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY nicht gefunden. "
                "Bitte .env Datei mit API-Key erstellen."
            )

        # Verzeichnisse erstellen
        settings = cls(
            anthropic_api_key=api_key,
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            # Learning DB Settings
            learning_db_type=os.getenv("LEARNING_DB_TYPE", "sqlite"),
            learning_db_url=os.getenv("LEARNING_DB_URL", ""),
            learning_db_fallback=os.getenv("LEARNING_DB_FALLBACK", "data/cases.db"),
            learning_db_timeout=int(os.getenv("LEARNING_DB_TIMEOUT", "5")),
            learning_db_retry=int(os.getenv("LEARNING_DB_RETRY", "3")),
            # PII Detection Settings
            pii_detection_enabled=os.getenv("PII_DETECTION_ENABLED", "true").lower() == "true",
            pii_detection_level=os.getenv("PII_DETECTION_LEVEL", "high"),
            pii_show_warnings=os.getenv("PII_SHOW_WARNINGS", "true").lower() == "true"
        )

        settings.data_dir.mkdir(exist_ok=True)
        settings.sessions_dir.mkdir(exist_ok=True)
        settings.changelogs_dir.mkdir(exist_ok=True)

        return settings


# Globale Settings-Instanz
_settings = None


def get_settings() -> Settings:
    """Settings Singleton"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings
