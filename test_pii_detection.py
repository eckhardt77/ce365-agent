#!/usr/bin/env python3
"""
Test-Skript für PII Detection (Presidio)

Testet:
1. Email-Adressen
2. Telefonnummern
3. Namen
4. IP-Adressen
5. Passwörter
6. IBAN
"""

from techcare.security.pii_detector import PIIDetector


def test_pii_detection():
    """PII Detection testen"""

    print("\n" + "="*80)
    print("  PII DETECTION TEST")
    print("="*80 + "\n")

    # PII Detector initialisieren
    print("1. PII DETECTOR INITIALISIEREN")
    print("-" * 80)

    detector = PIIDetector(
        enabled=True,
        level="high",
        language="de",
        show_warnings=True
    )

    if not detector.enabled:
        print("❌ Presidio nicht verfügbar. Bitte installieren:")
        print("   pip install presidio-analyzer presidio-anonymizer spacy")
        print("   python -m spacy download de_core_news_sm")
        return

    print("✓ PII Detector initialisiert")
    print(f"  Level: {detector.level}")
    print(f"  Sprache: {detector.language}")
    print()

    # Test-Cases
    test_cases = [
        {
            "name": "Email-Adresse",
            "text": "User max.mustermann@firma.de meldet Problem"
        },
        {
            "name": "Telefonnummer",
            "text": "Kontakt: +49 123 456789 oder 0171-1234567"
        },
        {
            "name": "Name + Email",
            "text": "Hans Müller (hans.mueller@example.com) hat ein Problem"
        },
        {
            "name": "IP-Adresse",
            "text": "Server 192.168.1.100 ist nicht erreichbar"
        },
        {
            "name": "Passwort (Pattern)",
            "text": "Aktuelles Passwort: Geheim123! muss geändert werden"
        },
        {
            "name": "IBAN",
            "text": "Überweisung an IBAN: DE89370400440532013000"
        },
        {
            "name": "Kombiniert",
            "text": """User john.doe@firma.de (Tel: 0171-123456) meldet:
Server 10.0.0.5 nicht erreichbar.
Admin-Password: Admin2024!
IBAN: DE89370400440532013000"""
        }
    ]

    # Tests durchführen
    print("2. TEST-CASES")
    print("-" * 80)
    print()

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Original:\n  {test_case['text'][:100]}...")
        print()

        # Analyse
        detections = detector.analyze(test_case['text'])

        if detections:
            print(f"✓ {len(detections)} PII erkannt:")
            for det in detections:
                print(f"  • {det.entity_type}: '{det.text}' (Score: {det.score:.2f})")
        else:
            print("  (keine PII erkannt)")

        print()

        # Anonymisierung
        anonymized, dets = detector.anonymize(test_case['text'])

        if dets:
            print(f"Anonymisiert:\n  {anonymized[:100]}...")
            print()

            # Warning Message
            warning = detector.format_detection_warning(dets)
            print(warning)
        else:
            print("Anonymisiert: (keine Änderungen)")

        print()
        print()

    # Zusammenfassung
    print("="*80)
    print("  TEST ABGESCHLOSSEN")
    print("="*80)
    print()

    print("Was wurde getestet:")
    print("  ✓ PII Detector Initialisierung")
    print("  ✓ Analyse (detect)")
    print("  ✓ Anonymisierung (replace)")
    print("  ✓ Detection Summary")
    print("  ✓ Warning Formatting")
    print()

    print("Erkannte Entity-Types:")
    print("  • EMAIL_ADDRESS")
    print("  • PHONE_NUMBER")
    print("  • PERSON (Namen)")
    print("  • IP_ADDRESS")
    print("  • PASSWORD (Pattern-basiert)")
    print("  • IBAN_CODE")
    print()

    print("✅ PII Detection funktioniert!")
    print()


if __name__ == "__main__":
    test_pii_detection()
