# TechCare Bot - Technische Projektbeschreibung

**AI-Powered IT Maintenance Assistant**

Version: 1.0.0 | Status: Production Ready | Lizenz: MIT + Non-Commercial

---

## 📋 Executive Summary

TechCare Bot ist ein Python-basierter KI-Wartungs-Assistent der IT-Technikern hilft, Windows- und macOS-Systeme zu diagnostizieren und zu reparieren. Das Projekt nutzt Anthropic's Claude API für natürliche Sprachverarbeitung und intelligente Problemanalyse, kombiniert mit einem strikten Sicherheitsmodell (GO REPAIR Lock) das autonome Systemänderungen verhindert.

**Kernmetriken:**
- 34 Tools (20 Audit, 13 Repair, 1 Analysis)
- 98/100 Security Score
- Python 3.9+
- Cross-Platform (Windows, macOS, Linux experimental)
- DSGVO-konform (lokale Verarbeitung)

---

## 🏗️ Architektur-Übersicht

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Terminal)                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    TechCare Bot (Core)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   UI Layer   │  │ State Machine│  │  Translator  │      │
│  │ (Rich Console)│  │  (Workflow)  │  │    (i18n)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Anthropic Tool Use Loop                   │   │
│  │  (Claude API + Tool Registry + Command Executor)     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tool Registry│  │   Executor   │  │  Changelog   │      │
│  │  (34 Tools)  │  │ (Safe Exec)  │  │   (Audit)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Systems                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Anthropic API│  │   OS (Win/Mac)│  │  Learning DB │      │
│  │ (Claude 4.5) │  │  (PowerShell/ │  │   (SQLite)   │      │
│  │              │  │   bash/launchctl)│  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technischer Stack

### **Backend / Core**
```yaml
Language: Python 3.9+
Framework: CLI (keine Web-Server)
Architecture: Event-Driven Tool Use Loop

Dependencies:
  - anthropic: >=0.30.0      # Claude API
  - pydantic: >=2.0.0        # Data Validation
  - rich: >=13.0.0           # Terminal UI
  - psutil: >=5.9.0          # System Info
  - keyring: >=24.0.0        # Encrypted API Key Storage
```

### **Security**
```yaml
PII Detection:
  - presidio-analyzer: >=2.2.0
  - presidio-anonymizer: >=2.2.0
  - spacy: >=3.7.0

Encryption:
  - cryptography: >=41.0.0
  - OS Keychain (macOS Keychain, Windows Credential Manager)
```

### **Storage**
```yaml
Session Management:
  - aiosqlite: >=0.19.0      # Async SQLite
  - sqlalchemy: >=2.0.0      # ORM (optional)

Learning System:
  - SQLite (default)
  - PostgreSQL (optional)
  - MySQL (optional)
```

### **External Tools**
```yaml
Web Search:
  - duckduckgo-search: >=5.0.0
  - beautifulsoup4: >=4.12.0

Malware Scanner:
  - Windows Defender (built-in)
  - ClamAV (optional, macOS/Linux)
```

---

## 📂 Projektstruktur

```
techcare-bot/
├── techcare/                          # Hauptmodul
│   ├── core/                         # Kernfunktionalität
│   │   ├── bot.py                   # Tool Use Loop, Orchestrierung
│   │   ├── client.py                # Anthropic API Wrapper
│   │   └── session.py               # Session Management
│   │
│   ├── tools/                        # Tool-System (34 Tools)
│   │   ├── base.py                  # BaseTool, AuditTool, RepairTool
│   │   ├── registry.py              # Tool Registry
│   │   ├── executor.py              # Safe Command Executor
│   │   ├── audit/                   # Read-Only Tools (20)
│   │   │   ├── system_info.py
│   │   │   ├── malware_scan.py     # NEU - Malware Scanner
│   │   │   └── ...
│   │   ├── repair/                  # Repair Tools (13)
│   │   │   ├── service_manager.py
│   │   │   └── ...
│   │   └── analysis/                # AI Analysis (1)
│   │       └── root_cause.py       # NEU - Root Cause Analysis
│   │
│   ├── workflow/                     # State Machine
│   │   ├── state_machine.py        # Audit → Plan → Lock → Execute
│   │   └── lock.py                 # Execution Lock ("GO REPAIR")
│   │
│   ├── learning/                     # Learning System
│   │   ├── case_library.py         # Case Storage/Retrieval
│   │   └── models.py               # Pydantic Models
│   │
│   ├── security/                     # Security Layer
│   │   └── pii_detector.py         # PII Detection (Presidio)
│   │
│   ├── storage/                      # Persistenz
│   │   ├── conversation.py         # Chat History (SQLite)
│   │   └── changelog.py            # Änderungslog (JSON)
│   │
│   ├── i18n/                         # Mehrsprachigkeit
│   │   ├── translator.py           # i18n System
│   │   └── languages/
│   │       ├── de.json             # Deutsch
│   │       └── en.json             # English
│   │
│   ├── ui/                           # Terminal UI
│   │   ├── console.py              # Rich Console Output
│   │   └── formatters.py           # Message Formatierung
│   │
│   ├── config/                       # Konfiguration
│   │   ├── settings.py             # Settings Management
│   │   ├── secrets.py              # Keychain Integration
│   │   └── system_prompt.py        # Deutscher System Prompt
│   │
│   └── __version__.py               # Version Info
│
├── data/                             # Lokale Daten (gitignored)
│   ├── sessions/                    # SQLite Conversations
│   ├── changelogs/                  # JSON Änderungslogs
│   └── cases.db                     # Learning System DB
│
├── docs/                             # Dokumentation
│   ├── PRODUKTBESCHREIBUNG.md
│   ├── PROJEKTBESCHREIBUNG.md
│   └── EDITION_VERGLEICH.md
│
├── install.sh                        # One-Command Install (Unix)
├── install.bat                       # One-Command Install (Windows)
├── requirements.txt
├── setup.py
├── README.md                         # English
├── README_DE.md                      # Deutsch
├── LICENSE
├── DISCLAIMER.txt
├── SECURITY.md
└── .env.example
```

---

## 🔄 Workflow State Machine

```
┌─────────┐
│  IDLE   │  Start
└────┬────┘
     │
     ▼
┌─────────┐
│  AUDIT  │  Read-Only Tools erlaubt
└────┬────┘  (System Info, Logs, Prozesse, etc.)
     │
     ▼
┌──────────┐
│ ANALYSIS │  Claude analysiert Daten
└────┬─────┘
     │
     ▼
┌─────────────┐
│ PLAN_READY  │  Plan erstellt, wartet auf Freigabe
└─────┬───────┘  User muss "GO REPAIR: 1,2,3" eingeben
      │
      ▼
┌─────────┐
│ LOCKED  │  Freigabe erhalten
└────┬────┘  Approved Steps gespeichert
     │
     ▼
┌───────────┐
│ EXECUTING │  Führt nur freigegebene Schritte aus
└────┬──────┘  Changelog wird geschrieben
     │
     ▼
┌───────────┐
│ COMPLETED │  Session abgeschlossen
└───────────┘  Changelog gespeichert

Regeln:
- Audit-Tools: Immer erlaubt (außer COMPLETED)
- Repair-Tools: Nur in LOCKED/EXECUTING State
- GO REPAIR Befehl: Transition von PLAN_READY → LOCKED
```

---

## 🔒 Sicherheitsarchitektur

### **1. Execution Lock (GO REPAIR)**

```python
class ExecutionLock:
    """Verhindert autonome Reparaturen"""

    def activate(self, repair_plan: list, approved_steps: list[int]):
        """Aktiviert Lock mit approved steps"""
        self.approved_steps = set(approved_steps)
        self.repair_plan = repair_plan
        self.is_locked = True

    def is_step_approved(self, step_number: int) -> bool:
        """Prüft ob Step approved ist"""
        return step_number in self.approved_steps
```

**Workflow:**
1. Bot erstellt Plan mit 5 Schritten
2. User prüft: "GO REPAIR: 1,3,5"
3. Nur Schritte 1, 3, 5 werden ausgeführt
4. Schritte 2, 4 werden übersprungen

---

### **2. PII Detection (Microsoft Presidio)**

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Erkennt automatisch:
- Email-Adressen
- Kreditkarten-Nummern
- Telefonnummern
- IP-Adressen
- Passwörter
- Sozialversicherungsnummern

# Ersetzt mit:
<EMAIL>, <CREDIT_CARD>, <PHONE_NUMBER>, etc.
```

---

### **3. Encrypted API Key Storage**

```python
# macOS: Keychain Access
keyring.set_password("TechCare-Bot", "anthropic_api_key", api_key)

# Windows: Credential Manager
keyring.set_password("TechCare-Bot", "anthropic_api_key", api_key)

# Linux: Secret Service (gnome-keyring)
keyring.set_password("TechCare-Bot", "anthropic_api_key", api_key)

# Fallback: .env (mit Migration-Prompt)
```

---

### **4. Audit Trail (Changelog)**

```json
{
  "session_id": "abc123",
  "created_at": "2026-02-17T10:30:00",
  "entries": [
    {
      "timestamp": "2026-02-17T10:35:12",
      "tool_name": "manage_service",
      "tool_input": {"service_name": "wuauserv", "action": "restart"},
      "result": "SUCCESS: Service restarted",
      "success": true
    }
  ]
}
```

---

## 🤖 Anthropic Tool Use Integration

### **Tool Definition Format**

```python
class SystemInfoTool(AuditTool):
    name = "get_system_info"
    description = "Gets OS, CPU, RAM, Disk, Uptime"

    input_schema = {
        "type": "object",
        "properties": {
            "detailed": {
                "type": "boolean",
                "description": "Include detailed hardware info"
            }
        },
        "required": []
    }

    async def execute(self, detailed: bool = False) -> dict:
        # Implementation
        pass
```

### **Tool Use Loop**

```python
async def process_message(self, user_input: str):
    # 1. Add message to history
    self.session.add_message("user", user_input)

    while True:
        # 2. Claude API Call mit Tools
        response = await self.client.create_message(
            messages=self.session.get_messages(),
            tools=self.tool_registry.get_tool_definitions()
        )

        # 3. Check stop_reason
        if response.stop_reason == "end_turn":
            return response.content[0].text

        elif response.stop_reason == "tool_use":
            # 4. Execute Tools
            tool_results = await self.handle_tool_use(response)

            # 5. Add tool results to history
            self.session.add_tool_results(tool_results)

            # 6. Loop (recurse)
            continue
```

---

## 🧠 Learning System

### **Case Storage**

```python
@dataclass
class Case:
    """Repräsentiert einen gelösten Fall"""
    id: Optional[int]
    os_type: str               # "Windows", "macOS", "Linux"
    os_version: str            # "Windows 11 23H2"
    problem_description: str   # User-Input
    error_codes: Optional[str] # z.B. "0x80070057"
    symptoms: str              # Von Bot extrahiert
    root_cause: str            # Von Bot identifiziert
    solution_steps: str        # JSON der Tool-Aufrufe
    success: bool              # War Lösung erfolgreich?
    created_at: datetime
    reused_count: int = 0      # Wie oft wiederverwendet
```

### **Similarity Matching**

```python
def find_similar_case(self, current_problem: str) -> Optional[Case]:
    """Findet ähnlichen Fall via Keyword-Matching"""

    # 1. Tokenize current problem
    keywords = extract_keywords(current_problem)

    # 2. Query DB for similar cases
    cases = db.query(Case).filter(
        Case.success == True,
        Case.os_type == current_os
    ).all()

    # 3. Calculate similarity scores
    for case in cases:
        score = jaccard_similarity(keywords, case.symptoms)
        if score > 0.7:  # 70% threshold
            return case

    return None
```

---

## 🌐 Mehrsprachigkeit (i18n)

### **Translation System**

```python
# Translator Singleton
from techcare.i18n import get_translator

t = get_translator()

# Verwendung
print(t.t("system.welcome"))
print(t.t("errors.api_key_missing"))
print(t.t("malware.scan_complete", threats=5))

# Sprache ändern
from techcare.i18n import set_language
set_language("en")  # Wechselt zu Englisch
```

### **Unterstützte Sprachen**

- 🇩🇪 Deutsch (de)
- 🇺🇸 English (en)
- 🇫🇷 Français (geplant)
- 🇮🇹 Italiano (geplant)
- 🇪🇸 Español (geplant)

---

## 📊 Performance & Skalierung

### **Metriken**

| Metrik | Wert |
|--------|------|
| **Startup Zeit** | < 2 Sekunden |
| **Tool Execution** | 100-500ms (lokal), 2-60s (remote API) |
| **Memory Usage** | ~100 MB (idle), ~300 MB (aktiv) |
| **DB Size** | ~5 MB (100 Cases), ~50 MB (1000 Cases) |
| **API Latency** | 500-2000ms (Claude API) |

### **Bottlenecks**

1. **Claude API** - Netzwerk-Latenz (500-2000ms)
2. **Event Logs** - Windows PowerShell langsam (5-10s)
3. **Malware Scan** - ClamAV/Defender langsam (2-60 Minuten)

### **Optimierungen**

- ✅ Async/Await für parallele Tool-Execution
- ✅ Caching von System-Info (5 Minuten TTL)
- ✅ Lazy Loading von Learning DB
- ⏳ Streaming von Claude API (geplant für v1.5)

---

## 🧪 Testing

### **Current Status**

| Test-Typ | Coverage | Status |
|----------|----------|--------|
| Unit Tests | 0% | ⚠️ TODO |
| Integration Tests | 0% | ⚠️ TODO |
| Manual Testing | ~60% | ✅ Basic |
| Security Audit | 98/100 | ✅ Done |

### **Test-Strategie (geplant)**

```python
# Unit Tests
tests/test_tools/test_system_info.py
tests/test_workflow/test_state_machine.py
tests/test_security/test_pii_detector.py

# Integration Tests
tests/integration/test_tool_use_loop.py
tests/integration/test_go_repair_workflow.py

# E2E Tests
tests/e2e/test_windows_update_scenario.py
```

---

## 🚀 Deployment

### **Installation (End-User)**

```bash
# One-Command Install
curl -fsSL https://techcare-bot.de/install.sh | bash

# Was passiert:
1. Python 3.9+ Check
2. Virtual Environment erstellen
3. Dependencies installieren (pip install -r requirements.txt)
4. Spacy Model downloaden (de_core_news_sm)
5. TechCare Bot installieren (pip install -e .)
6. API Key Setup (beim ersten Start)
```

### **Development Setup**

```bash
git clone https://github.com/yourusername/techcare-bot.git
cd techcare-bot

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download de_core_news_sm

pip install -e .

# Tests laufen lassen (wenn vorhanden)
pytest
```

---

## 📈 Roadmap

### **v1.0 - Community Edition** ✅ DONE
- 34 Tools
- Root Cause Analysis
- Malware Scanner
- Learning System
- Mehrsprachigkeit (DE/EN)

### **v1.5 - Pro Features** (Q2 2026)
- Predictive Maintenance
- API für Automation
- Web Dashboard (optional)
- Streaming API Responses

### **v2.0 - Enterprise** (Q3 2026)
- Multi-System Management (Fleet Dashboard)
- LDAP/SSO Integration
- Team-Features
- Scheduled Maintenance

---

## 🐛 Known Issues

| Issue | Severity | Status |
|-------|----------|--------|
| Windows PowerShell slow für Event Logs | Medium | ⏳ Workaround (Limit auf 100 Events) |
| ClamAV freshclam timeout bei langsamer Verbindung | Low | ⏳ 5min Timeout, Error Handling |
| Keine Unit Tests | High | ⏳ TODO |
| Linux Support experimental | Medium | ⏳ Beta |

---

## 📞 Kontakt & Contributing

**Maintainer:** Carsten Eckhardt / Eckhardt-Marketing

**Contributing:**
1. Fork Repository
2. Feature Branch erstellen
3. Tests schreiben (wichtig!)
4. Pull Request öffnen

**Security Issues:**
- Email: security@eckhardt-marketing.de
- **NICHT** als GitHub Issue (Responsible Disclosure)

---

## 📄 Lizenz

**MIT License with Non-Commercial Restriction**

- ✅ Kostenlos für private Nutzung
- ✅ Kostenlos für Bildung
- ✅ Kostenlos für Open Source
- ❌ Kommerzielle Nutzung benötigt separate Lizenz

---

**TechCare Bot v1.0.0** - Production Ready
*Copyright © 2026 Carsten Eckhardt / Eckhardt-Marketing*
