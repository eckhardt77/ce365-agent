#!/usr/bin/env python3
"""
CE365 Agent - Paket-Creator für Firmendeployment

Erstellt ein vorkonfiguriertes Installationspaket:
- .env mit Firmen-Config (Provider, API-Key, Lizenz)
- install.sh
- Alle benötigten Dateien

Usage:
    python scripts/create_package.py \
        --company "Musterfirma GmbH" \
        --license-key "CE365-PRO-ABC123" \
        --provider anthropic \
        --api-key "sk-ant-..." \
        --output ./packages/musterfirma/

    python scripts/create_package.py --test
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def create_package(
    company: str,
    license_key: str,
    provider: str = "anthropic",
    api_key: str = "",
    db_url: str = "",
    output_dir: str = "./package",
):
    """Erstellt Firmen-Installationspaket"""
    output = Path(output_dir)

    if output.exists():
        print(f"⚠️  Verzeichnis {output} existiert bereits.")
        response = input("Überschreiben? (ja/nein): ").strip().lower()
        if response not in ["ja", "j", "yes", "y"]:
            print("Abgebrochen.")
            return False
        shutil.rmtree(output)

    output.mkdir(parents=True)

    # Projekt-Root
    project_root = Path(__file__).parent.parent

    # 1. ce365/ Package kopieren
    src_ce365 = project_root / "ce365"
    dst_ce365 = output / "ce365"
    shutil.copytree(src_ce365, dst_ce365, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"✓ ce365/ kopiert")

    # 2. Requirements + Setup
    for f in ["requirements.txt", "pyproject.toml", "setup.py", "DISCLAIMER.txt", "LICENSE"]:
        src = project_root / f
        if src.exists():
            shutil.copy2(src, output / f)

    # 3. install.sh
    shutil.copy2(project_root / "install.sh", output / "install.sh")
    os.chmod(output / "install.sh", 0o755)

    # 4. Vorkonfigurierte .env erstellen
    env_content = f"""# ============================================================================
# CE365 Agent - Vorkonfiguriert für {company}
# ============================================================================

# LLM Provider
LLM_PROVIDER={provider}

# API Keys
"""
    key_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    for p, env_var in key_map.items():
        value = api_key if p == provider else ""
        env_content += f"{env_var}={value}\n"

    env_content += f"""
# Model
LLM_MODEL={"claude-sonnet-4-5-20250929" if provider == "anthropic" else "gpt-4o" if provider == "openai" else "anthropic/claude-sonnet-4-5-20250929"}

LOG_LEVEL=INFO

# Learning
LEARNING_DB_TYPE={"postgresql" if db_url else "sqlite"}
LEARNING_DB_URL={db_url}
LEARNING_DB_FALLBACK=data/cases.db
LEARNING_DB_TIMEOUT=5
LEARNING_DB_RETRY=3

# Security
PII_DETECTION_ENABLED=true
PII_DETECTION_LEVEL=high
PII_SHOW_WARNINGS=true

# License
EDITION=pro
LICENSE_KEY={license_key}
LICENSE_SERVER_URL=

# Technician (wird beim ersten Start gesetzt)
TECHNICIAN_PASSWORD_HASH=
SESSION_TIMEOUT=3600
"""

    (output / ".env").write_text(env_content)
    os.chmod(output / ".env", 0o600)
    print(f"✓ .env erstellt (Provider: {provider})")

    # 5. README
    readme = f"""# CE365 Agent — {company}

## Installation

```bash
chmod +x install.sh
./install.sh
```

## Starten

```bash
source venv/bin/activate
python -m ce365
```

## Konfiguration

Die `.env` Datei ist bereits vorkonfiguriert.
Beim ersten Start wird ein Techniker-Passwort gesetzt.
"""
    (output / "README.md").write_text(readme)

    print(f"\n✅ Paket erstellt: {output}")
    print(f"   Firma: {company}")
    print(f"   Provider: {provider}")
    print(f"   Lizenz: {license_key[:15]}...")
    print(f"\n   Verteilen: Verzeichnis als ZIP an Techniker senden.")

    return True


def test_package():
    """Test-Paket erstellen"""
    print("🧪 Erstelle Test-Paket...")
    success = create_package(
        company="Test GmbH",
        license_key="CE365-PRO-TEST-12345",
        provider="anthropic",
        api_key="sk-ant-test-key",
        output_dir="/tmp/ce365-test-package",
    )
    if success:
        print("\n✓ Test-Paket erfolgreich erstellt unter /tmp/ce365-test-package/")
        # Aufräumen
        shutil.rmtree("/tmp/ce365-test-package")
        print("✓ Test-Paket aufgeräumt")


def main():
    parser = argparse.ArgumentParser(description="CE365 Paket-Creator für Firmendeployment")
    parser.add_argument("--company", help="Firmenname")
    parser.add_argument("--license-key", help="Lizenzschlüssel")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai", "openrouter"])
    parser.add_argument("--api-key", default="", help="API Key")
    parser.add_argument("--db-url", default="", help="PostgreSQL URL für Shared Learning")
    parser.add_argument("--output", default="./package", help="Ausgabe-Verzeichnis")
    parser.add_argument("--test", action="store_true", help="Test-Paket erstellen")

    args = parser.parse_args()

    if args.test:
        test_package()
        return

    if not args.company or not args.license_key:
        parser.error("--company und --license-key sind erforderlich")

    create_package(
        company=args.company,
        license_key=args.license_key,
        provider=args.provider,
        api_key=args.api_key,
        db_url=args.db_url,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
