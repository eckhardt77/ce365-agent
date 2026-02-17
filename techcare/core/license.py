"""
TechCare Bot - License Validation Module

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Validiert Lizenzschlüssel mit zentralem License Server
"""

import asyncio
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

    def __init__(self, backend_url: str, cache_dir: Path = None):
        """
        Args:
            backend_url: URL zum Backend (via VPN/Cloudflare/Tailscale)
            cache_dir: Verzeichnis für gecachte Lizenzen
        """
        self.backend_url = backend_url.rstrip("/")
        self.cache_dir = cache_dir or Path.home() / ".techcare" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "license.json"

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
                "edition": str,  # "community", "pro", "pro_business", "enterprise"
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
        """Speichert Lizenz-Validierung im Cache"""
        cache_data = {
            "license_key": license_key,
            "result": result,
            "cached_at": datetime.now().isoformat()
        }

        try:
            self.cache_file.write_text(
                json.dumps(cache_data, indent=2)
            )
        except Exception:
            pass  # Cache-Fehler ignorieren

    def _load_cached_license(self, license_key: str) -> Optional[Dict]:
        """
        Lädt gecachte Lizenz (Offline-Fallback)

        Returns:
            Lizenz-Info wenn gültig, sonst None
        """
        if not self.cache_file.exists():
            return None

        try:
            cache_data = json.loads(self.cache_file.read_text())

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
        edition: "community", "pro", "pro_business", "enterprise"
        feature: "shared_learning", "unlimited_systems", "monitoring", etc.

    Returns:
        True wenn Feature verfügbar
    """
    features_map = {
        "community": [
            # Max 10 Reparaturen/Monat, 1 System, lokales Learning
        ],
        "pro": [
            "unlimited_repairs",  # Unbegrenzte Reparaturen
            # 1 System, lokales Learning
        ],
        "pro_business": [
            "unlimited_repairs",
            "unlimited_systems",  # Unbegrenzte Systeme
            "monitoring",  # Sensor-Mode
            # Lokales Learning
        ],
        "enterprise": [
            "unlimited_repairs",
            "unlimited_systems",
            "monitoring",
            "shared_learning",  # Gemeinsame Wissensdatenbank
            "team_features",  # Team-Management
        ]
    }

    return feature in features_map.get(edition, [])
