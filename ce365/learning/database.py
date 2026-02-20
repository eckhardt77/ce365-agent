"""
CE365 Agent - Database Abstraction Layer

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Unterstützt:
- SQLite (lokal)
- PostgreSQL (remote)
- MySQL/MariaDB (remote)
- Automatischer Fallback
- Connection Pooling
- Retry-Logik
"""

import time
from typing import Optional
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, Index, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from ce365.config.settings import get_settings

Base = declarative_base()


class CaseModel(Base):
    """SQLAlchemy Model für Cases"""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(String(32), nullable=False)
    os_type = Column(String(20), nullable=False, index=True)
    os_version = Column(String(50))
    problem_description = Column(Text, nullable=False)
    error_codes = Column(String(200))
    symptoms = Column(Text)
    root_cause = Column(Text)
    diagnosis_confidence = Column(Float)
    audit_data = Column(Text)
    solution_plan = Column(Text)
    executed_steps = Column(Text)
    success = Column(Boolean, default=True, index=True)
    session_id = Column(String(50), nullable=False, unique=True)
    tokens_used = Column(Integer)
    duration_minutes = Column(Integer)
    reuse_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)

    __table_args__ = (
        Index('idx_os_success', 'os_type', 'success'),
    )


class KeywordModel(Base):
    """SQLAlchemy Model für Keywords"""
    __tablename__ = "case_keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False, index=True)
    keyword = Column(String(100), nullable=False, index=True)

    __table_args__ = (
        Index('idx_keyword_case', 'keyword', 'case_id'),
    )


class DatabaseManager:
    """
    Database Manager für Learning System

    Features:
    - Automatische Auswahl: PostgreSQL oder SQLite
    - Connection Pooling
    - Retry-Logik mit Fallback
    - Schema-Migration
    """

    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        self._is_remote = False
        self._fallback_active = False

        self._initialize_connection()

    def _initialize_connection(self):
        """Connection initialisieren mit Fallback"""

        # Remote DB versuchen (wenn konfiguriert)
        if self.settings.learning_db_type in ["postgresql", "mysql"] and self.settings.learning_db_url:
            if self._try_remote_connection():
                return

        # Fallback zu SQLite
        self._setup_sqlite_fallback()

    def _try_remote_connection(self) -> bool:
        """
        Remote PostgreSQL/MySQL Connection versuchen

        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        retry_count = 0
        max_retries = self.settings.learning_db_retry

        while retry_count < max_retries:
            try:
                # DB-URL: async Treiber durch sync Treiber ersetzen
                db_url = self.settings.learning_db_url
                db_url = db_url.replace("mysql+asyncmy://", "mysql+pymysql://")
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

                # Engine erstellen (PostgreSQL oder MySQL)
                engine_kwargs = {
                    'poolclass': QueuePool,
                    'pool_size': 5,
                    'max_overflow': 10,
                    'pool_timeout': self.settings.learning_db_timeout,
                    'pool_pre_ping': True,  # Connection Check vor Nutzung
                    'echo': False
                }

                # MySQL spezifische Settings
                if 'mysql' in db_url.lower():
                    engine_kwargs['connect_args'] = {
                        'connect_timeout': self.settings.learning_db_timeout
                    }

                self.engine = create_engine(
                    db_url,
                    **engine_kwargs
                )

                # Connection testen
                with self.engine.connect() as conn:
                    # Test-Query (funktioniert für PostgreSQL und MySQL)
                    conn.execute(text("SELECT 1"))

                # Schema erstellen (falls noch nicht vorhanden)
                Base.metadata.create_all(self.engine)

                # Session Factory
                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )

                self._is_remote = True
                self._fallback_active = False

                db_type = "MySQL" if 'mysql' in self.settings.learning_db_url.lower() else "PostgreSQL"
                print(f"✓ Remote {db_type} Learning-DB verbunden: {self._mask_password(self.settings.learning_db_url)}")
                return True

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⚠️  Remote-DB Verbindungsfehler (Versuch {retry_count}/{max_retries}): {str(e)[:100]}")
                    time.sleep(1)  # Kurze Pause vor Retry
                else:
                    print(f"❌ Remote-DB nicht erreichbar nach {max_retries} Versuchen: {str(e)[:100]}")

        return False

    def _setup_sqlite_fallback(self):
        """SQLite Fallback einrichten"""
        try:
            # Verzeichnis erstellen
            db_path = Path(self.settings.learning_db_fallback)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # SQLite Engine
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                poolclass=NullPool,  # SQLite: kein Pooling nötig
                echo=False
            )

            # Schema erstellen
            Base.metadata.create_all(self.engine)

            # Session Factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            self._is_remote = False
            self._fallback_active = True

            if self.settings.learning_db_type in ["postgresql", "mysql"]:
                print(f"⚠️  Fallback zu lokalem SQLite: {db_path}")
            else:
                print(f"✓ Lokales SQLite Learning-DB: {db_path}")

        except Exception as e:
            raise RuntimeError(f"Konnte weder Remote-DB noch Fallback initialisieren: {e}")

    def get_session(self) -> Session:
        """
        Session holen

        Returns:
            SQLAlchemy Session
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database nicht initialisiert")

        return self.SessionLocal()

    def is_remote(self) -> bool:
        """Prüft ob Remote-DB aktiv ist"""
        return self._is_remote

    def is_fallback_active(self) -> bool:
        """Prüft ob Fallback aktiv ist"""
        return self._fallback_active

    def retry_remote_connection(self) -> bool:
        """
        Retry Remote Connection (z.B. nach Netzwerk-Unterbrechung)

        Returns:
            True wenn Remote wieder verfügbar
        """
        if self._is_remote:
            return True  # Bereits verbunden

        print("🔄 Versuche Remote-DB erneut zu verbinden...")
        if self._try_remote_connection():
            print("✓ Remote-DB Verbindung wiederhergestellt")
            return True

        print("❌ Remote-DB weiterhin nicht erreichbar")
        return False

    @staticmethod
    def _mask_password(url: str) -> str:
        """Password in URL maskieren für Logs"""
        if "@" in url and "://" in url:
            # Split an letztem @ (Passwort kann @ nicht enthalten, Host schon nicht)
            at_idx = url.rfind("@")
            cred_part = url[:at_idx]      # z.B. "mysql+asyncmy://user:P@ss:wort"
            host_part = url[at_idx + 1:]  # z.B. "host:3306/db"
            proto_sep = cred_part.find("://")
            if proto_sep != -1:
                protocol = cred_part[:proto_sep]
                user_pass = cred_part[proto_sep + 3:]  # z.B. "user:P@ss:wort"
                colon_idx = user_pass.find(":")
                if colon_idx != -1:
                    user = user_pass[:colon_idx]
                    return f"{protocol}://{user}:****@{host_part}"
        return url


# Globale Instanz
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Database Manager Singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
