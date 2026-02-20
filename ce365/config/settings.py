import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional


def _get_binary_dir() -> Optional[Path]:
    """Gibt das Verzeichnis der Binary zurück (bei PyInstaller)"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return None


def _get_external_config_path() -> Optional[Path]:
    """Pfad zur externen Config-Datei neben der Binary"""
    binary_dir = _get_binary_dir()
    if binary_dir:
        return binary_dir / "ce365.cfg"
    return None


def _load_external_config() -> dict:
    """
    Lädt Config aus ce365.cfg neben der Binary (portable Kunden-Paket).
    Format: KEY=VALUE (wie .env)
    """
    cfg_path = _get_external_config_path()
    if not cfg_path or not cfg_path.exists():
        return {}

    config = {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    config[key.strip()] = value.strip()
    except Exception:
        pass
    return config


def _extract_embedded_to_external():
    """
    Extrahiert embedded Config in eine externe ce365.cfg-Datei.
    Wird beim ersten Start einer Kunden-Binary aufgerufen.
    """
    cfg_path = _get_external_config_path()
    if not cfg_path:
        return

    try:
        from ce365.setup.embedded_config import is_embedded, get_config
        if not is_embedded():
            return

        config = get_config()
        if not config:
            return

        lines = [
            "# CE365 Agent — Kunden-Konfiguration",
            "# Automatisch extrahiert aus eingebetteter Config",
            "# Diese Datei NICHT löschen — wird für Updates benötigt",
            "",
        ]

        # Techniker-Metadaten
        tech_name = config.pop("_TECHNICIAN_NAME", "Techniker")
        company = config.pop("_COMPANY", "")
        config.pop("_SENSITIVE_KEYS", None)

        lines.append(f"# Techniker: {tech_name}")
        if company:
            lines.append(f"# Firma: {company}")
        lines.append("")

        # Metadaten als Config-Werte speichern
        lines.append(f"_TECHNICIAN_NAME={tech_name}")
        if company:
            lines.append(f"_COMPANY={company}")
        lines.append("")

        # Alle Config-Werte
        for key, value in config.items():
            if not key.startswith("_") and value:
                lines.append(f"{key}={value}")

        cfg_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(cfg_path, 0o600)

    except Exception:
        pass  # Fehler beim Extrahieren sind nicht fatal


# === Config laden (Priorität: externe cfg > embedded > .env) ===

_PORTABLE_CONFIG = {}

# 1. Externe Config neben Binary (höchste Priorität für portable Binary)
_PORTABLE_CONFIG = _load_external_config()

if not _PORTABLE_CONFIG:
    # 2. Embedded Config prüfen (Kunden-Paket, erster Start)
    try:
        from ce365.setup.embedded_config import is_embedded, get_config
        if is_embedded():
            _PORTABLE_CONFIG = get_config()
            # Beim ersten Start: Config extrahieren für zukünftige Updates
            _extract_embedded_to_external()
    except ImportError:
        pass

if _PORTABLE_CONFIG:
    # Portable Config als Environment-Variablen setzen
    for key, value in _PORTABLE_CONFIG.items():
        if not key.startswith("_") and value:
            os.environ[key] = str(value)
else:
    # 3. Standard .env laden (Techniker-PC / pip-Installation)
    binary_dir = _get_binary_dir()
    if binary_dir:
        load_dotenv(binary_dir / "config" / ".env", override=True)
    else:
        load_dotenv()

# Secrets Manager importieren
try:
    from ce365.config.secrets import get_secrets_manager
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False


class Settings(BaseModel):
    """Globale Einstellungen für CE365 Agent"""

    # LLM Provider
    llm_provider: str = "anthropic"  # "anthropic", "openai", "openrouter"
    llm_model: str = "claude-sonnet-4-6"  # Provider-abhängig

    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # Logging
    log_level: str = "INFO"

    # Language
    language: str = "de"  # "de" oder "en"

    # Pfade
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    sessions_dir: Path = data_dir / "sessions"
    changelogs_dir: Path = data_dir / "changelogs"
    config_file: Path = Path.home() / ".ce365" / "config.json"

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

    # License Server
    license_server_url: str = ""  # URL zum Lizenzserver

    # License
    edition: str = "community"  # "community", "pro"
    license_key: str = ""  # Lizenzschlüssel

    # Technician Security
    technician_password_hash: str = ""  # bcrypt hash des Techniker-Passworts
    session_timeout: int = 3600  # Session-Timeout in Sekunden (1 Stunde)

    # Portable Binary Metadata
    technician_name: str = ""
    company: str = ""

    @classmethod
    def load(cls) -> "Settings":
        """Settings aus Environment-Variablen und Config-Datei laden"""

        # .env neu laden (wichtig: Wizard erstellt .env nach dem ersten Import)
        if not _PORTABLE_CONFIG:
            binary_dir = _get_binary_dir()
            if binary_dir:
                load_dotenv(binary_dir / "config" / ".env", override=True)
            else:
                load_dotenv(override=True)

        # Config-Datei laden (falls vorhanden)
        user_config = cls._load_user_config()

        # Provider bestimmen
        llm_provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

        # API Key laden: Priorität Keychain > .env
        anthropic_key = ""
        openai_key = os.getenv("OPENAI_API_KEY", "")
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

        if SECRETS_MANAGER_AVAILABLE:
            secrets = get_secrets_manager()
            anthropic_key = secrets.get_api_key() or ""

        if not anthropic_key:
            anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        # Prüfe ob der gewählte Provider einen Key hat
        provider_keys = {
            "anthropic": anthropic_key,
            "openai": openai_key,
            "openrouter": openrouter_key,
        }
        active_key = provider_keys.get(llm_provider, "")
        if not active_key:
            raise ValueError(
                f"Kein API Key für Provider '{llm_provider}' gefunden. "
                "Bitte beim ersten Start konfigurieren oder .env Datei erstellen."
            )

        # Techniker-Metadaten: .env > Portable Config
        tech_name = os.getenv("TECHNICIAN_NAME", "") or _PORTABLE_CONFIG.get("_TECHNICIAN_NAME", "")
        company = os.getenv("COMPANY", "") or _PORTABLE_CONFIG.get("_COMPANY", "")

        # Verzeichnisse erstellen
        settings = cls(
            llm_provider=llm_provider,
            llm_model=os.getenv("LLM_MODEL", os.getenv("CLAUDE_MODEL", None)),
            anthropic_api_key=anthropic_key,
            openai_api_key=openai_key,
            openrouter_api_key=openrouter_key,
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
            # License Server
            license_server_url=os.getenv("LICENSE_SERVER_URL", ""),
            # License Settings
            edition=os.getenv("EDITION", "community"),
            license_key=os.getenv("LICENSE_KEY", ""),
            # Security Settings
            technician_password_hash=os.getenv("TECHNICIAN_PASSWORD_HASH", ""),
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600")),
            # Portable Metadata
            technician_name=tech_name,
            company=company,
        )

        # Verzeichnisse mit restriktiven Berechtigungen erstellen
        for d in [settings.data_dir, settings.sessions_dir, settings.changelogs_dir]:
            d.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(d, 0o700)
            except OSError:
                pass

        ce365_home = settings.config_file.parent
        ce365_home.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(ce365_home, 0o700)
        except OSError:
            pass

        return settings

    @staticmethod
    def _load_user_config() -> dict:
        """Lädt User-Config aus ~/.ce365/config.json"""
        config_file = Path.home() / ".ce365" / "config.json"

        if not config_file.exists():
            return {}

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self):
        """Speichert User-Settings in ~/.ce365/config.json"""
        config = {
            "language": self.language,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "log_level": self.log_level
        }

        self.config_file.parent.mkdir(exist_ok=True)
        try:
            os.chmod(self.config_file.parent, 0o700)
        except OSError:
            pass

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        try:
            os.chmod(self.config_file, 0o600)
        except OSError:
            pass

    def is_portable(self) -> bool:
        """Prüft ob wir als portable Kunden-Binary laufen"""
        return bool(_PORTABLE_CONFIG)


# Globale Settings-Instanz
_settings = None


def get_settings() -> Settings:
    """Settings Singleton"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings
