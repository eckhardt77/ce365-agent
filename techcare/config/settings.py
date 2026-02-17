import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# .env laden (Fallback)
load_dotenv()

# Secrets Manager importieren
try:
    from techcare.config.secrets import get_secrets_manager
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False


class Settings(BaseModel):
    """Globale Einstellungen für TechCare Bot"""

    # API
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"

    # Logging
    log_level: str = "INFO"

    # Language
    language: str = "de"  # "de" oder "en"

    # Pfade
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    sessions_dir: Path = data_dir / "sessions"
    changelogs_dir: Path = data_dir / "changelogs"
    config_file: Path = Path.home() / ".techcare" / "config.json"

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

    # Network Connection (für Remote Services)
    backend_url: str = ""  # URL zum Backend (via VPN/Cloudflare/Tailscale)
    network_method: str = "direct"  # "cloudflare", "tailscale", "vpn", "direct"

    # License
    edition: str = "community"  # "community", "pro", "pro_business", "enterprise"
    license_key: str = ""  # Lizenzschlüssel

    # Technician Security
    technician_password_hash: str = ""  # bcrypt hash des Techniker-Passworts
    session_timeout: int = 3600  # Session-Timeout in Sekunden (1 Stunde)

    @classmethod
    def load(cls) -> "Settings":
        """Settings aus Environment-Variablen und Config-Datei laden"""

        # Config-Datei laden (falls vorhanden)
        user_config = cls._load_user_config()

        # API Key laden: Priorität Keychain > .env
        api_key = None

        if SECRETS_MANAGER_AVAILABLE:
            secrets = get_secrets_manager()
            api_key = secrets.get_api_key()

            # Info wo Key herkommt
            storage_method = secrets.get_storage_method()
            if storage_method == "env_plaintext" and secrets.keyring_available:
                # Migration anbieten
                print("ℹ️  API Key liegt unverschlüsselt in .env")
                print("   Führe 'techcare --migrate-key' aus um zu OS Keychain zu migrieren")

        # Fallback: Direkt aus os.getenv (wenn secrets nicht verfügbar)
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY nicht gefunden. "
                "Bitte beim ersten Start konfigurieren oder .env Datei erstellen."
            )

        # Verzeichnisse erstellen
        settings = cls(
            anthropic_api_key=api_key,
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            language=user_config.get("language", "de"),  # Aus User Config
            # Learning DB Settings
            learning_db_type=os.getenv("LEARNING_DB_TYPE", "sqlite"),
            learning_db_url=os.getenv("LEARNING_DB_URL", ""),
            learning_db_fallback=os.getenv("LEARNING_DB_FALLBACK", "data/cases.db"),
            learning_db_timeout=int(os.getenv("LEARNING_DB_TIMEOUT", "5")),
            learning_db_retry=int(os.getenv("LEARNING_DB_RETRY", "3")),
            # PII Detection Settings
            pii_detection_enabled=os.getenv("PII_DETECTION_ENABLED", "true").lower() == "true",
            pii_detection_level=os.getenv("PII_DETECTION_LEVEL", "high"),
            pii_show_warnings=os.getenv("PII_SHOW_WARNINGS", "true").lower() == "true",
            # Network Settings
            backend_url=os.getenv("BACKEND_URL", ""),
            network_method=os.getenv("NETWORK_METHOD", "direct"),
            # License Settings
            edition=os.getenv("EDITION", "community"),
            license_key=os.getenv("LICENSE_KEY", ""),
            # Security Settings
            technician_password_hash=os.getenv("TECHNICIAN_PASSWORD_HASH", ""),
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600"))
        )

        settings.data_dir.mkdir(exist_ok=True)
        settings.sessions_dir.mkdir(exist_ok=True)
        settings.changelogs_dir.mkdir(exist_ok=True)
        settings.config_file.parent.mkdir(exist_ok=True)

        return settings

    @staticmethod
    def _load_user_config() -> dict:
        """Lädt User-Config aus ~/.techcare/config.json"""
        config_file = Path.home() / ".techcare" / "config.json"

        if not config_file.exists():
            return {}

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        """Speichert User-Settings in ~/.techcare/config.json"""
        config = {
            "language": self.language,
            "claude_model": self.claude_model,
            "log_level": self.log_level
        }

        self.config_file.parent.mkdir(exist_ok=True)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)


# Globale Settings-Instanz
_settings = None


def get_settings() -> Settings:
    """Settings Singleton"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings
