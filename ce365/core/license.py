"""
CE365 Agent - License Validation Module

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Validiert Lizenzschlüssel mit zentralem License Server
"""

import asyncio
import hashlib
import hmac
import httpx
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta


class LicenseValidator:
    """
    Validiert Lizenzschlüssel mit Remote License Server

    Features:
    - Online-Validierung via Backend
    - Offline-Fallback mit gecachter Lizenz
    - Timeout Handling
    """

    # HMAC key derived from machine-specific data (not a secret, but prevents simple file copy)
    _CACHE_HMAC_SALT = b"ce365-license-cache-v1"

    def __init__(self, license_server_url: str, cache_dir: Path = None):
        """
        Args:
            license_server_url: URL zum Lizenzserver
            cache_dir: Verzeichnis für gecachte Lizenzen
        """
        self.license_server_url = license_server_url.rstrip("/")
        self.cache_dir = cache_dir or Path.home() / ".ce365" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "license.json"
        self._hmac_key = self._derive_hmac_key()

    def _derive_hmac_key(self) -> bytes:
        """Leitet HMAC-Key aus System-spezifischen Daten ab"""
        import uuid
        import platform
        machine_data = f"{uuid.getnode()}|{platform.node()}|{platform.machine()}"
        return hashlib.sha256(
            self._CACHE_HMAC_SALT + machine_data.encode()
        ).digest()

    def _compute_hmac(self, data: str) -> str:
        """Berechnet HMAC für Cache-Daten"""
        return hmac.new(self._hmac_key, data.encode(), hashlib.sha256).hexdigest()

    def _verify_hmac(self, data: str, signature: str) -> bool:
        """Verifiziert HMAC-Signatur"""
        expected = self._compute_hmac(data)
        return hmac.compare_digest(expected, signature)

    async def validate(
        self,
        license_key: str,
        system_fingerprint: str = None,
        timeout: int = 10
    ) -> Dict:
        """
        Validiert Lizenzschlüssel mit System-Fingerprint

        Args:
            license_key: Lizenzschlüssel
            system_fingerprint: Hardware-basierter System-Fingerprint (optional)
            timeout: Request-Timeout in Sekunden

        Returns:
            {
                "valid": bool,
                "edition": str,  # "community", "pro"
                "expires_at": str,  # ISO timestamp oder "never"
                "max_systems": int,  # 0 = unlimited
                "registered_systems": int,  # Anzahl registrierter Systeme
                "customer_name": str,
                "error": str  # wenn valid=False
            }
        """
        # 1. Versuche Online-Validierung
        try:
            result = await self._validate_online(license_key, system_fingerprint, timeout)

            # Cache aktualisieren bei Erfolg
            if result["valid"]:
                self._cache_license(license_key, result)

            return result

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            # 2. Offline-Fallback
            cached = self._load_cached_license(license_key)

            if cached:
                return cached

            # 3. Keine gecachte Lizenz vorhanden
            return {
                "valid": False,
                "error": f"License Server nicht erreichbar und keine gecachte Lizenz vorhanden: {str(e)}"
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Fehler bei Lizenzvalidierung: {str(e)}"
            }

    async def _validate_online(
        self,
        license_key: str,
        system_fingerprint: str,
        timeout: int
    ) -> Dict:
        """Online-Validierung via Backend mit System-Fingerprint"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            payload = {
                "license_key": license_key
            }

            # System-Fingerprint mitschicken (für System-Limit Check)
            if system_fingerprint:
                payload["system_fingerprint"] = system_fingerprint

            response = await client.post(
                f"{self.license_server_url}/api/license/validate",
                json=payload
            )

            if response.status_code != 200:
                return {
                    "valid": False,
                    "error": f"License Server Fehler: HTTP {response.status_code}"
                }

            data = response.json()
            return data

    def _cache_license(self, license_key: str, result: Dict):
        """Speichert Lizenz-Validierung im Cache mit HMAC-Signatur"""
        # Sensible Daten entfernen — nur das Minimum cachen
        safe_result = {
            "valid": result.get("valid"),
            "edition": result.get("edition"),
            "expires_at": result.get("expires_at"),
        }

        cache_data = {
            "license_key_hash": hashlib.sha256(license_key.encode()).hexdigest(),
            "result": safe_result,
            "cached_at": datetime.now().isoformat()
        }

        try:
            payload = json.dumps(cache_data, sort_keys=True)
            signed_data = {
                "payload": payload,
                "signature": self._compute_hmac(payload)
            }
            self.cache_file.write_text(json.dumps(signed_data, indent=2))
            import os
            os.chmod(self.cache_file, 0o600)
        except Exception:
            pass  # Cache-Fehler ignorieren

    def _load_cached_license(self, license_key: str) -> Optional[Dict]:
        """
        Lädt gecachte Lizenz (Offline-Fallback) mit HMAC-Verifikation

        Returns:
            Lizenz-Info wenn gültig, sonst None
        """
        if not self.cache_file.exists():
            return None

        try:
            signed_data = json.loads(self.cache_file.read_text())

            # HMAC-Signatur verifizieren
            payload = signed_data.get("payload")
            signature = signed_data.get("signature")
            if not payload or not signature or not self._verify_hmac(payload, signature):
                # Cache manipuliert oder ungültiges Format
                self.cache_file.unlink(missing_ok=True)
                return None

            cache_data = json.loads(payload)

            # Prüfe ob gecachte Lizenz zum aktuellen Key passt (Hash-Vergleich)
            key_hash = hashlib.sha256(license_key.encode()).hexdigest()
            cached_key = cache_data.get("license_key_hash") or cache_data.get("license_key", "")
            if cached_key != key_hash and cached_key != license_key:
                return None

            # Prüfe ob Cache zu alt ist (max 24 Stunden)
            # Verhindert Offline-Missbrauch: User MUSS alle 24h online validieren
            cached_at = datetime.fromisoformat(cache_data["cached_at"])
            if datetime.now() - cached_at > timedelta(hours=24):
                return None

            result = cache_data["result"]

            # Prüfe ob Lizenz abgelaufen ist
            if result.get("expires_at") and result["expires_at"] != "never":
                expires_at = datetime.fromisoformat(result["expires_at"])
                if datetime.now() > expires_at:
                    return {
                        "valid": False,
                        "error": "Lizenz abgelaufen (Offline-Cache)"
                    }

            # Füge Hinweis hinzu dass Offline-Cache verwendet wird
            result["_offline"] = True
            result["_cached_at"] = cache_data["cached_at"]

            return result

        except Exception:
            return None


class SessionManager:
    """
    Verwaltet Lizenz-Sessions mit dem License Server

    - Session starten (Seat belegen)
    - Heartbeats senden (alle 5 Min)
    - Session freigeben beim Beenden
    """

    HEARTBEAT_INTERVAL = 300  # 5 Minuten

    def __init__(self, license_server_url: str, license_key: str):
        self.license_server_url = license_server_url.rstrip("/")
        self.license_key = license_key
        self.session_token: Optional[str] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    def _get_system_fingerprint(self) -> str:
        """Erzeugt einen System-Fingerprint"""
        import uuid
        import platform
        machine_data = f"{uuid.getnode()}|{platform.node()}|{platform.machine()}"
        return hashlib.sha256(machine_data.encode()).hexdigest()[:16]

    async def start_session(self, timeout: int = 10) -> Dict:
        """
        Startet eine Session beim Lizenzserver

        Returns:
            {"success": bool, "session_token": str, "error": str}
        """
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.license_server_url}/api/license/session/start",
                    json={
                        "license_key": self.license_key,
                        "system_fingerprint": self._get_system_fingerprint(),
                    },
                )

                if response.status_code != 200:
                    return {"success": False, "error": f"HTTP {response.status_code}"}

                data = response.json()
                if data.get("success"):
                    self.session_token = data.get("session_token", "")
                return data

        except (httpx.TimeoutException, httpx.ConnectError):
            return {"success": False, "error": "License Server nicht erreichbar"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_heartbeat(self, timeout: int = 10) -> bool:
        """Sendet einen einzelnen Heartbeat"""
        if not self.session_token:
            return False

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.license_server_url}/api/license/session/heartbeat",
                    json={"session_token": self.session_token},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("success", False)
                return False
        except Exception:
            return False

    async def _heartbeat_loop(self):
        """Hintergrund-Loop für periodische Heartbeats"""
        while True:
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
            await self.send_heartbeat()

    def start_heartbeat_timer(self):
        """Startet den Heartbeat-Timer als asyncio Task"""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop())

    def stop_heartbeat_timer(self):
        """Stoppt den Heartbeat-Timer"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def release_session(self, timeout: int = 5) -> bool:
        """
        Gibt die Session beim Lizenzserver frei

        Returns:
            True wenn erfolgreich
        """
        self.stop_heartbeat_timer()

        if not self.session_token:
            return True

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.license_server_url}/api/license/session/release",
                    json={"session_token": self.session_token},
                )
                self.session_token = None
                return response.status_code == 200
        except Exception:
            self.session_token = None
            return False


def validate_license_sync(
    license_key: str,
    license_server_url: str,
    timeout: int = 10
) -> Dict:
    """
    Synchrone Lizenzvalidierung (für den Wizard)

    Args:
        license_key: Lizenzschlüssel
        license_server_url: Lizenzserver URL
        timeout: Request-Timeout

    Returns:
        Lizenz-Info Dict
    """
    try:
        import httpx as httpx_sync
        with httpx_sync.Client(timeout=timeout) as client:
            response = client.post(
                f"{license_server_url.rstrip('/')}/api/license/validate",
                json={"license_key": license_key},
            )

            if response.status_code != 200:
                return {
                    "valid": False,
                    "error": f"License Server Fehler: HTTP {response.status_code}",
                }

            return response.json()

    except (httpx_sync.TimeoutException, httpx_sync.ConnectError):
        return {
            "valid": False,
            "error": "License Server nicht erreichbar. Bitte Internetverbindung prüfen.",
        }
    except Exception as e:
        return {"valid": False, "error": f"Fehler: {str(e)}"}


async def validate_license(
    license_key: str,
    license_server_url: str,
    system_fingerprint: str = None,
    timeout: int = 10
) -> Dict:
    """
    Helper-Funktion für Lizenzvalidierung mit System-Fingerprint

    Args:
        license_key: Lizenzschlüssel
        license_server_url: Lizenzserver URL
        system_fingerprint: System-Fingerprint (für System-Limit Check)
        timeout: Request-Timeout

    Returns:
        Lizenz-Info Dict
    """
    validator = LicenseValidator(license_server_url)
    return await validator.validate(license_key, system_fingerprint, timeout)


def check_edition_features(edition: str, feature: str) -> bool:
    """
    Prüft ob Edition ein Feature unterstützt

    Args:
        edition: "community", "pro"
        feature: Feature-Name (siehe features_map)

    Returns:
        True wenn Feature verfügbar
    """
    features_map = {
        "community": [
            "local_learning",  # Lokales Learning (SQLite)
            "pii_detection",  # PII Detection
            # Basis-Audit (7 Tools), 5 Remediation Runs/Monat
            # Nicht-kommerzielle Nutzung
        ],
        "pro": [
            "local_learning",
            "pii_detection",
            "unlimited_repairs",  # Unbegrenzte Remediation Runs
            "advanced_audit",  # Stress-Tests, Malware, Temp, Drivers, Report
            "advanced_repair",  # SFC, Network, Updates, Startup, Restore
            "web_search",  # Web-Suche fuer Problemloesung
            "root_cause_analysis",  # KI Root-Cause-Analyse
            "system_report",  # HTML System-Report
            "driver_management",  # Treiber-Check
            "commercial_use",  # Kommerzielle Nutzung erlaubt
            "shared_learning",  # Gemeinsame Wissensdatenbank (PostgreSQL)
            "hooks",  # Workflow-Hooks (PRE/POST Repair, Session)
            "file_reading",  # Dateien lesen (Log-Analyse, Config)
            "ssh_remote",  # SSH/Remote-Zugriff
            "mcp_integration",  # MCP-Server-Anbindung
            "system_control",  # Reboot, Software, User, File Management
            # 1 Seat per License
        ],
    }

    return feature in features_map.get(edition, [])
