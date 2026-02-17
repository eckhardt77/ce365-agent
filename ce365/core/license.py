"""
CE365 Agent - License Validation Module

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

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

    def __init__(self, backend_url: str, cache_dir: Path = None):
        """
        Args:
            backend_url: URL zum Backend (via VPN/Cloudflare/Tailscale)
            cache_dir: Verzeichnis für gecachte Lizenzen
        """
        self.backend_url = backend_url.rstrip("/")
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
                "edition": str,  # "free", "pro", "business"
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
                f"{self.backend_url}/api/license/validate",
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
        cache_data = {
            "license_key": license_key,
            "result": result,
            "cached_at": datetime.now().isoformat()
        }

        try:
            payload = json.dumps(cache_data, sort_keys=True)
            signed_data = {
                "payload": payload,
                "signature": self._compute_hmac(payload)
            }
            self.cache_file.write_text(json.dumps(signed_data, indent=2))
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

            # Prüfe ob gecachte Lizenz zum aktuellen Key passt
            if cache_data["license_key"] != license_key:
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


async def validate_license(
    license_key: str,
    backend_url: str,
    system_fingerprint: str = None,
    timeout: int = 10
) -> Dict:
    """
    Helper-Funktion für Lizenzvalidierung mit System-Fingerprint

    Args:
        license_key: Lizenzschlüssel
        backend_url: Backend URL
        system_fingerprint: System-Fingerprint (für System-Limit Check)
        timeout: Request-Timeout

    Returns:
        Lizenz-Info Dict
    """
    validator = LicenseValidator(backend_url)
    return await validator.validate(license_key, system_fingerprint, timeout)


def check_edition_features(edition: str, feature: str) -> bool:
    """
    Prüft ob Edition ein Feature unterstützt

    Args:
        edition: "free", "pro", "business"
        feature: Feature-Name (siehe features_map)

    Returns:
        True wenn Feature verfügbar
    """
    features_map = {
        "free": [
            "local_learning",  # Lokales Learning (SQLite)
            "pii_detection",  # PII Detection
            # Basis-Audit (7 Tools), 5 Remediation Runs/Monat
            # Evaluation / nicht-kommerzielle Nutzung
        ],
        "pro": [
            "local_learning",
            "pii_detection",
            "unlimited_repairs",  # Unbegrenzte Remediation Runs
            "advanced_audit",  # Stress-Tests, Malware, Temp, Drivers, Report
            "advanced_repair",  # SFC, Network, Updates, Startup, Restore
            "web_search",  # Web-Suche für Problemlösung
            "root_cause_analysis",  # KI Root-Cause-Analyse
            "system_report",  # HTML System-Report
            "driver_management",  # Treiber-Check
            "commercial_use",  # Kommerzielle Nutzung erlaubt
            # 1 Seat, 1 aktive Session, max 10 Systeme/30 Tage
        ],
        "business": [
            "local_learning",
            "pii_detection",
            "unlimited_repairs",
            "advanced_audit",
            "advanced_repair",
            "web_search",
            "root_cause_analysis",
            "system_report",
            "driver_management",
            "commercial_use",
            "unlimited_systems",  # Unbegrenzte Systeme
            "monitoring",  # Sensor-Mode (Dauerbetrieb)
            "shared_learning",  # Gemeinsame Wissensdatenbank (PostgreSQL)
            "team_features",  # Policies, Runbooks, Branding
        ]
    }

    return feature in features_map.get(edition, [])
