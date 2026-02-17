#!/usr/bin/env python3
"""
Test-Skript für Setup Wizard

Simuliert User-Input für automatischen Test
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch
from ce365.setup.wizard import SetupWizard


def test_wizard_needs_setup():
    """Test 1: Prüft ob Wizard Setup-Bedarf erkennt"""
    print("=" * 80)
    print("TEST 1: Setup-Bedarf prüfen")
    print("=" * 80)

    wizard = SetupWizard()

    # .env sollte nicht existieren (wurde umbenannt)
    needs = wizard.needs_setup()

    if needs:
        print("✓ Wizard erkennt fehlende .env")
    else:
        print("❌ Wizard sollte Setup-Bedarf erkennen")
        return False

    print()
    return True


def test_wizard_env_creation():
    """Test 2: Prüft .env Erstellung"""
    print("=" * 80)
    print("TEST 2: .env Erstellung")
    print("=" * 80)

    wizard = SetupWizard()

    # Mock User-Input
    test_data = {
        "user_name": "Test User",
        "company": "Test Company",
        "api_key": "sk-ant-api03-test-key-123456789",
        "briefing": "Test Setup"
    }

    success = wizard._create_env_file(**test_data)

    if success:
        print("✓ .env Datei erstellt")

        # Prüfen ob Datei existiert
        if Path(".env").exists():
            print("✓ .env existiert")

            # Inhalt prüfen
            content = Path(".env").read_text()

            checks = [
                ("API Key", test_data["api_key"] in content),
                ("User Name", test_data["user_name"] in content),
                ("Company", test_data["company"] in content),
                ("Briefing", test_data["briefing"] in content),
            ]

            all_ok = True
            for name, result in checks:
                if result:
                    print(f"✓ {name} in .env")
                else:
                    print(f"❌ {name} fehlt in .env")
                    all_ok = False

            return all_ok
        else:
            print("❌ .env existiert nicht")
            return False
    else:
        print("❌ .env Erstellung fehlgeschlagen")
        return False


def test_wizard_template():
    """Test 3: Prüft Template-Loading"""
    print()
    print("=" * 80)
    print("TEST 3: Template Loading")
    print("=" * 80)

    wizard = SetupWizard()

    # Default Template
    template = wizard._get_default_template()

    if "ANTHROPIC_API_KEY" in template:
        print("✓ Default Template enthält API Key")
    else:
        print("❌ Default Template fehlt API Key")
        return False

    if "LEARNING_DB_TYPE" in template:
        print("✓ Default Template enthält Learning DB Config")
    else:
        print("❌ Default Template fehlt Learning DB Config")
        return False

    print()
    return True


def cleanup():
    """Cleanup nach Tests"""
    print("=" * 80)
    print("CLEANUP")
    print("=" * 80)

    # Test-.env löschen
    if Path(".env").exists():
        Path(".env").unlink()
        print("✓ Test-.env gelöscht")

    # Backup wiederherstellen
    if Path(".env.backup").exists():
        Path(".env.backup").rename(".env")
        print("✓ Original .env wiederhergestellt")

    print()


def main():
    """Führt alle Tests aus"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "SETUP WIZARD TEST SUITE" + " " * 35 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    tests = [
        ("Setup-Bedarf", test_wizard_needs_setup),
        ("Template", test_wizard_template),
        (".env Erstellung", test_wizard_env_creation),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {str(e)}")
            results.append((name, False))

    # Cleanup
    cleanup()

    # Zusammenfassung
    print("=" * 80)
    print("TEST-ZUSAMMENFASSUNG")
    print("=" * 80)

    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:8} {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print()
    print(f"Ergebnis: {passed}/{total} Tests bestanden")

    if passed == total:
        print("\n✅ Alle Tests erfolgreich!\n")
        return 0
    else:
        print(f"\n❌ {total - passed} Test(s) fehlgeschlagen!\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
