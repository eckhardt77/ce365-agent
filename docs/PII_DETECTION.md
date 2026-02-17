# PII Detection - Datenschutz & DSGVO-Compliance

**Automatische Erkennung und Anonymisierung sensibler Daten**

---

## 🛡️ **Was ist PII Detection?**

**PII = Personally Identifiable Information** (Personenbezogene Daten)

CE365 Agent nutzt **Microsoft Presidio**, um automatisch sensible Informationen zu erkennen und zu anonymisieren:

- 📧 **Email-Adressen**
- 📱 **Telefonnummern**
- 🆔 **Personennamen**
- 🌐 **IP-Adressen**
- 🔑 **Passwörter** (Pattern-basiert)
- 💳 **Kreditkarten, IBAN**
- 📍 **Adressen**
- 🆔 **Ausweisdokumente**

---

## 🎯 **Warum wichtig?**

### **1. DSGVO-Compliance**
- ✅ Art. 5 DSGVO: Datenminimierung
- ✅ Art. 25 DSGVO: Privacy by Design
- ✅ Art. 32 DSGVO: Technische Maßnahmen

### **2. Sicherheit**
- ❌ Ohne PII: Passwörter in Logs, Claude API, Learning DB
- ✅ Mit PII: Automatische Anonymisierung

### **3. Team-Learning**
- ❌ Ohne PII: Andere Techniker sehen sensible Daten
- ✅ Mit PII: Nur anonymisierte Cases im Team

### **4. Compliance für Enterprise-Kunden**
- ✅ Banking, Healthcare, Government
- ✅ ISO 27001 Zertifizierung
- ✅ SOC 2 Compliance

---

## 🔧 **Funktionsweise**

### **Flow: User Input → PII Detection → Claude API**

```
┌─────────────────────────────────────────────┐
│  User Input (RAW)                           │
│  "User hans.mueller@firma.de hat Problem,   │
│   Passwort: Geheim123!"                     │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  PII Detection (Presidio)                   │
│  ├── Analyzer: Erkenne PII                  │
│  │   • EMAIL: hans.mueller@firma.de         │
│  │   • PASSWORD: Geheim123!                 │
│  └── Anonymizer: Ersetze PII                │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  Anonymisiert                               │
│  "User <EMAIL_ADDRESS> hat Problem,         │
│   Passwort: <PASSWORD>"                     │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  User Warning (optional)                    │
│  ⚠️ 2 sensible Informationen anonymisiert: │
│     • Email-Adresse (1x)                    │
│     • Passwort (1x)                         │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  ✓ Claude API                               │
│  ✓ Learning System                          │
│  ✓ Changelog                                │
│  → Nur anonymisierte Daten!                 │
└─────────────────────────────────────────────┘
```

---

## ⚙️ **Konfiguration**

### **`.env` Einstellungen:**

```bash
# PII Detection aktivieren (empfohlen!)
PII_DETECTION_ENABLED=true

# Detection Level: high/medium/low
PII_DETECTION_LEVEL=high

# User-Warnings anzeigen
PII_SHOW_WARNINGS=true
```

### **Detection Levels:**

```
┌──────────────┬────────────────────────────────────┐
│ Level        │ Erkannte Entity-Types              │
├──────────────┼────────────────────────────────────┤
│ HIGH         │ Alle PII (Email, Phone, Person,    │
│ (Standard)   │ IP, Password, IBAN, Credit Card,   │
│              │ Location, Date, URL, etc.)         │
├──────────────┼────────────────────────────────────┤
│ MEDIUM       │ Wichtige PII (Email, Phone,        │
│              │ Person, IP, Password, IBAN,        │
│              │ Credit Card)                       │
├──────────────┼────────────────────────────────────┤
│ LOW          │ Kritische PII (Password, IBAN,     │
│              │ Credit Card, SSN)                  │
└──────────────┴────────────────────────────────────┘
```

**Empfehlung:**
- **Production:** `HIGH` (maximaler Schutz)
- **Development:** `MEDIUM` (Balance)
- **Testing:** `LOW` oder `false` (Performance)

---

## 🧪 **Testing**

### **Test-Script ausführen:**

```bash
source venv/bin/activate
python test_pii_detection.py
```

**Erwartete Ausgabe:**

```
================================================================================
  PII DETECTION TEST
================================================================================

1. PII DETECTOR INITIALISIEREN
--------------------------------------------------------------------------------
✓ PII Detector initialisiert
  Level: high
  Sprache: de

2. TEST-CASES
--------------------------------------------------------------------------------

Test 1: Email-Adresse
----------------------------------------
Original:
  User max.mustermann@firma.de meldet Problem

✓ 1 PII erkannt:
  • EMAIL_ADDRESS: 'max.mustermann@firma.de' (Score: 0.85)

Anonymisiert:
  User <EMAIL_ADDRESS> meldet Problem

⚠️  1 sensible Information erkannt und anonymisiert:
   • Email-Adresse (1x)

...

✅ PII Detection funktioniert!
```

---

## 📊 **Erkannte Entity-Types**

### **Standard (Presidio)**

| Entity Type | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `EMAIL_ADDRESS` | Email-Adressen | max@firma.de |
| `PHONE_NUMBER` | Telefonnummern | +49 171 123456, 0171-123456 |
| `PERSON` | Personennamen | Max Mustermann |
| `IP_ADDRESS` | IPv4/IPv6 Adressen | 192.168.1.1, ::1 |
| `CREDIT_CARD` | Kreditkartennummern | 4532-1234-5678-9010 |
| `IBAN_CODE` | IBAN | DE89370400440532013000 |
| `LOCATION` | Adressen | Hauptstr. 1, 12345 Berlin |
| `URL` | URLs | https://example.com |
| `DATE_TIME` | Datum/Zeit | 17.02.2026, 14:30 |
| `CRYPTO` | Crypto-Wallets | 1A1zP1eP5QGefi2DMPTfTL... |

### **Custom Recognizers**

| Entity Type | Beschreibung | Pattern |
|-------------|--------------|---------|
| `PASSWORD` | Passwort-Patterns | Geheim123!, Pass@word |

---

## 🔒 **Security Best Practices**

### **1. Immer aktiviert in Production**
```bash
PII_DETECTION_ENABLED=true
PII_DETECTION_LEVEL=high
```

### **2. Audit-Logs prüfen**
```bash
# Regelmäßig checken ob PII durchrutscht
grep -i "password\|email\|phone" data/changelogs/*.json
```

### **3. Learning DB prüfen**
```bash
# Stichproben in Case Library
sqlite3 data/cases.db "SELECT problem_description FROM cases LIMIT 10"
# Sollte keine echten Emails/Namen enthalten
```

### **4. False Positives**
```
Wenn legitime Begriffe erkannt werden (z.B. "Max" als Name):
→ Detection Level auf "medium" reduzieren
→ Oder Custom Whitelisting implementieren
```

---

## 🌍 **Multi-Language Support**

### **Unterstützte Sprachen:**

```python
# Deutsch (Standard)
detector = PIIDetector(language="de")

# Englisch
detector = PIIDetector(language="en")
```

**Hinweis:** Spacy Sprachmodelle müssen installiert sein:

```bash
# Deutsch
python -m spacy download de_core_news_sm

# Englisch
python -m spacy download en_core_web_sm
```

---

## 📈 **Performance**

### **Overhead:**

```
Ohne PII Detection:
  process_message(): ~200ms

Mit PII Detection:
  PII Analyze: ~50-100ms
  PII Anonymize: ~10-20ms
  Total: ~270-320ms

Overhead: +70-120ms (~35-60%)
```

**Optimierung:**
- Detection Level `medium` statt `high` → -30ms
- Nur bei User-Input, nicht bei Assistant-Output
- Lazy Loading (erste Analyse dauert länger)

### **Caching:**

Presidio cached intern, zweiter Aufruf ist schneller:

```
1. Analyse: 100ms
2. Analyse: 20ms (5x schneller)
```

---

## 🐛 **Troubleshooting**

### **Problem: "Presidio nicht verfügbar"**

**Ursache:** Presidio nicht installiert

**Lösung:**
```bash
pip install presidio-analyzer presidio-anonymizer spacy
python -m spacy download de_core_news_sm
```

---

### **Problem: "ModuleNotFoundError: No module named 'en_core_web_sm'"**

**Ursache:** Spacy Sprachmodell fehlt

**Lösung:**
```bash
python -m spacy download de_core_news_sm
python -m spacy download en_core_web_sm
```

---

### **Problem: False Positives (z.B. "Max" wird als PERSON erkannt)**

**Lösung 1: Level reduzieren**
```bash
PII_DETECTION_LEVEL=medium  # Weniger aggressive Erkennung
```

**Lösung 2: Custom Whitelist** (TODO)
```python
detector.whitelist = ["Max", "Min", "Test"]
```

---

### **Problem: False Negatives (PII wird nicht erkannt)**

**Lösung: Level erhöhen**
```bash
PII_DETECTION_LEVEL=high
```

**Oder:** Custom Recognizers hinzufügen (siehe Presidio Docs)

---

## 🎁 **Enterprise Features (Pro Version)**

In CE365 Pro geplant:

- 🔄 **De-Anonymization** - Original-Daten für Techniker abrufbar (mit Berechtigung)
- 📊 **PII Dashboard** - Statistiken über erkannte PII
- 🎯 **Custom Recognizers** - Firmen-spezifische PII (z.B. Kundennummern)
- 🔐 **Encrypted Storage** - Verschlüsselte Speicherung von Mappings
- 📋 **Audit-Log** - Wer hat wann welche PII gesehen

---

## 📚 **Weitere Informationen**

- **Presidio Docs:** https://microsoft.github.io/presidio/
- **DSGVO:** https://dsgvo-gesetz.de/
- **ISO 27001:** https://www.iso.org/isoiec-27001-information-security.html

---

**Implementiert:** 2026-02-17
**Version:** v0.5.0 (mit PII Detection)
**Status:** ✅ Production-Ready
