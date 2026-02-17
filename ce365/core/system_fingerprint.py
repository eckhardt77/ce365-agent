"""
CE365 Agent - System Fingerprinting

Generiert eindeutigen Hardware-basierten Fingerprint für Lizenz-Enforcement
"""

import hashlib
import platform
import uuid
from pathlib import Path
from typing import Optional


def get_system_fingerprint() -> str:
    """
    Generiert eindeutigen System-Fingerprint

    Kombiniert:
    - MAC-Adresse (primär)
    - CPU-Architektur
    - Hostname
    - System-UUID (wenn verfügbar)

    Returns:
        SHA256-Hash als Hex-String
    """
    components = []

    # 1. MAC-Adresse (primär)
    try:
        mac = uuid.getnode()
        components.append(str(mac))
    except Exception:
        pass

    # 2. CPU-Architektur
    components.append(platform.machine())

    # 3. Hostname
    components.append(platform.node())

    # 4. System-UUID (Linux/Windows)
    try:
        # Linux: /etc/machine-id
        machine_id_file = Path("/etc/machine-id")
        if machine_id_file.exists():
            components.append(machine_id_file.read_text().strip())

        # Windows: Systeminfo
        elif platform.system() == "Windows":
            import subprocess
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                uuid_line = result.stdout.strip().split("\n")[1].strip()
                components.append(uuid_line)
    except Exception:
        pass

    # 5. Kombiniere und hashe
    fingerprint_raw = "|".join(components)
    fingerprint_hash = hashlib.sha256(fingerprint_raw.encode()).hexdigest()

    return fingerprint_hash


def get_cached_fingerprint() -> Optional[str]:
    """
    Lädt gecachten Fingerprint (für Stabilität)

    Returns:
        Gecachter Fingerprint oder None
    """
    cache_file = Path.home() / ".ce365" / "fingerprint"

    if cache_file.exists():
        try:
            return cache_file.read_text().strip()
        except Exception:
            pass

    return None


def save_fingerprint(fingerprint: str):
    """Speichert Fingerprint im Cache"""
    cache_file = Path.home() / ".ce365" / "fingerprint"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        cache_file.write_text(fingerprint)
    except Exception:
        pass


def get_or_create_fingerprint() -> str:
    """
    Holt gecachten Fingerprint oder erstellt neuen

    Returns:
        System-Fingerprint
    """
    # Versuche gecachten Fingerprint zu laden
    cached = get_cached_fingerprint()
    if cached:
        return cached

    # Erstelle neuen Fingerprint
    fingerprint = get_system_fingerprint()

    # Cache für zukünftige Nutzung
    save_fingerprint(fingerprint)

    return fingerprint
