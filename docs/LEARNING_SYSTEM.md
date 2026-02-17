# CE365 Agent - Learning & Memory System

## 🧠 Konzept-Übersicht

CE365 soll aus vergangenen Fällen **lernen** und **bekannte Probleme schneller lösen**.

### Vision

```
Erstes Mal: "Windows Update Fehler 0x80070002"
→ Vollständiger Audit-Workflow
→ Diagnose: 10 Minuten
→ Lösung gefunden: Service + Cache

Zweites Mal: "Windows Update Fehler 0x80070002"
→ CE365 erkennt Problem sofort!
→ "Ich kenne dieses Problem bereits!"
→ Schnelle Lösung: 2 Minuten
→ Bietet bewährten Plan an
```

---

## 🏗️ Architektur

### 3-Stufen Learning System

```
┌─────────────────────────────────────────────────────────┐
│  STUFE 1: Case Library (Lokal)                          │
│  ─────────────────────────────────────────────────────  │
│  • SQLite-Datenbank mit gelösten Fällen                 │
│  • Problem → Lösung Mapping                             │
│  • Success Rate Tracking                                │
│  • Schnelle Keyword-Suche                               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  STUFE 2: RAG (Retrieval-Augmented Generation)          │
│  ─────────────────────────────────────────────────────  │
│  • Embedding-basierte Ähnlichkeitssuche                 │
│  • Vector-Datenbank (ChromaDB/FAISS)                    │
│  • Semantische Problem-Erkennung                        │
│  • Top-K ähnliche Fälle finden                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  STUFE 3: Dynamic Context Injection                     │
│  ─────────────────────────────────────────────────────  │
│  • Relevante Fälle in System Prompt injizieren          │
│  • Claude bekommt Kontext aus Vergangenheit             │
│  • Schnellere und präzisere Diagnose                    │
│  • Bewährte Lösungen bevorzugen                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Datenbank-Schema

### Tabelle: `cases`

```sql
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Problem
    os_type TEXT NOT NULL,              -- 'windows' oder 'macos'
    os_version TEXT,                    -- 'Windows 11', 'macOS 15'
    problem_description TEXT NOT NULL,  -- User's Problem-Beschreibung
    error_codes TEXT,                   -- z.B. '0x80070002'
    symptoms TEXT,                      -- Symptome als JSON

    -- Diagnose
    root_cause TEXT NOT NULL,           -- Identifizierte Root Cause
    diagnosis_confidence FLOAT,         -- 0.0-1.0
    audit_data TEXT,                    -- Audit-Outputs als JSON

    -- Lösung
    solution_plan TEXT NOT NULL,        -- Reparatur-Plan
    executed_steps TEXT,                -- Ausgeführte Schritte als JSON
    success BOOLEAN DEFAULT FALSE,      -- War Lösung erfolgreich?

    -- Meta
    session_id TEXT UNIQUE,
    tokens_used INTEGER,
    duration_minutes INTEGER,

    -- Embeddings (für RAG)
    problem_embedding BLOB,             -- Vector für Similarity Search

    -- Learning
    reuse_count INTEGER DEFAULT 0,      -- Wie oft wurde Lösung wiederverwendet?
    success_rate FLOAT DEFAULT 0.0      -- Erfolgsquote bei Wiederverwendung
);

CREATE INDEX idx_os_type ON cases(os_type);
CREATE INDEX idx_error_codes ON cases(error_codes);
CREATE INDEX idx_success ON cases(success);
```

### Tabelle: `case_keywords`

```sql
CREATE TABLE case_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    keyword TEXT NOT NULL,
    weight FLOAT DEFAULT 1.0,           -- Wichtigkeit des Keywords
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE INDEX idx_keyword ON case_keywords(keyword);
```

### Tabelle: `playbooks`

```sql
CREATE TABLE playbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    os_type TEXT NOT NULL,

    -- Pattern Matching
    problem_pattern TEXT,               -- Regex für Problem-Erkennung
    error_code_pattern TEXT,            -- z.B. '0x8007.*'

    -- Lösung
    solution_steps TEXT NOT NULL,       -- JSON: [{step, command, risk}]
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 Feature 1: Case Library (Einfach)

### Workflow

```
1. User beschreibt Problem
   ↓
2. CE365 sucht in Case Library
   - Keyword-Match
   - OS-Match
   - Error-Code-Match
   ↓
3. Falls Match gefunden (>80% Ähnlichkeit):
   "Ich kenne dieses Problem bereits!"
   "Letztes Mal hat folgende Lösung funktioniert: ..."
   "Soll ich den bewährten Plan verwenden?"
   ↓
4. User: "Ja" → Schneller Plan
   User: "Nein" → Vollständiger Audit
```

### Implementation

```python
# ce365/learning/case_library.py

import sqlite3
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Case:
    """Gespeicherter Fall"""
    id: Optional[int]
    os_type: str
    os_version: str
    problem_description: str
    error_codes: Optional[str]
    root_cause: str
    solution_plan: str
    executed_steps: str
    success: bool
    session_id: str
    created_at: datetime

    reuse_count: int = 0
    success_rate: float = 0.0


class CaseLibrary:
    """
    Case Library für gespeicherte Fälle

    Features:
    - Speichern erfolgreicher Lösungen
    - Suchen ähnlicher Fälle
    - Success Rate Tracking
    """

    def __init__(self, db_path: str = "data/cases.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Datenbank initialisieren"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cases Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                os_type TEXT NOT NULL,
                os_version TEXT,
                problem_description TEXT NOT NULL,
                error_codes TEXT,
                symptoms TEXT,
                root_cause TEXT NOT NULL,
                diagnosis_confidence FLOAT,
                audit_data TEXT,
                solution_plan TEXT NOT NULL,
                executed_steps TEXT,
                success BOOLEAN DEFAULT FALSE,
                session_id TEXT UNIQUE,
                tokens_used INTEGER,
                duration_minutes INTEGER,
                reuse_count INTEGER DEFAULT 0,
                success_rate FLOAT DEFAULT 0.0
            )
        """)

        # Keywords Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                keyword TEXT NOT NULL,
                weight FLOAT DEFAULT 1.0,
                FOREIGN KEY (case_id) REFERENCES cases(id)
            )
        """)

        # Indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_os_type ON cases(os_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_codes ON cases(error_codes)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON case_keywords(keyword)")

        conn.commit()
        conn.close()

    def save_case(self, case: Case) -> int:
        """Fall speichern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cases (
                os_type, os_version, problem_description, error_codes,
                root_cause, solution_plan, executed_steps, success, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case.os_type, case.os_version, case.problem_description,
            case.error_codes, case.root_cause, case.solution_plan,
            case.executed_steps, case.success, case.session_id
        ))

        case_id = cursor.lastrowid

        # Keywords extrahieren und speichern
        keywords = self._extract_keywords(case.problem_description)
        for keyword in keywords:
            cursor.execute("""
                INSERT INTO case_keywords (case_id, keyword)
                VALUES (?, ?)
            """, (case_id, keyword))

        conn.commit()
        conn.close()

        return case_id

    def find_similar_cases(
        self,
        os_type: str,
        problem_description: str,
        error_code: Optional[str] = None,
        limit: int = 5
    ) -> List[Case]:
        """
        Ähnliche Fälle finden

        Matching-Kriterien:
        1. OS-Type Match (Pflicht)
        2. Error-Code Match (wenn vorhanden)
        3. Keyword-Overlap (Gewichtet)
        4. Nur erfolgreiche Fälle
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Keywords aus Problem extrahieren
        keywords = self._extract_keywords(problem_description)

        # Query aufbauen
        query = """
            SELECT DISTINCT c.*,
                   COUNT(k.keyword) as keyword_matches
            FROM cases c
            LEFT JOIN case_keywords k ON c.id = k.case_id
            WHERE c.os_type = ?
              AND c.success = TRUE
        """

        params = [os_type]

        # Error-Code Filter
        if error_code:
            query += " AND c.error_codes LIKE ?"
            params.append(f"%{error_code}%")

        # Keyword Filter
        if keywords:
            placeholders = ",".join("?" * len(keywords))
            query += f" AND k.keyword IN ({placeholders})"
            params.extend(keywords)

        query += """
            GROUP BY c.id
            ORDER BY keyword_matches DESC, c.success_rate DESC, c.reuse_count DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        # Cases erstellen
        cases = []
        for row in rows:
            case = Case(
                id=row[0],
                os_type=row[2],
                os_version=row[3],
                problem_description=row[4],
                error_codes=row[5],
                root_cause=row[7],
                solution_plan=row[10],
                executed_steps=row[11],
                success=bool(row[12]),
                session_id=row[13],
                created_at=datetime.fromisoformat(row[1]),
                reuse_count=row[16],
                success_rate=row[17]
            )
            cases.append(case)

        return cases

    def mark_case_reused(self, case_id: int, success: bool):
        """
        Fall als wiederverwendet markieren

        Aktualisiert:
        - reuse_count
        - success_rate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Aktuellen Stand holen
        cursor.execute("""
            SELECT reuse_count, success_rate
            FROM cases
            WHERE id = ?
        """, (case_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        reuse_count, success_rate = row

        # Neue Success Rate berechnen
        new_reuse_count = reuse_count + 1
        new_success_rate = (success_rate * reuse_count + (1.0 if success else 0.0)) / new_reuse_count

        # Update
        cursor.execute("""
            UPDATE cases
            SET reuse_count = ?,
                success_rate = ?
            WHERE id = ?
        """, (new_reuse_count, new_success_rate, case_id))

        conn.commit()
        conn.close()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Keywords aus Text extrahieren

        Einfache Version:
        - Lowercase
        - Min 3 Zeichen
        - Keine Stopwords
        """
        stopwords = {
            'der', 'die', 'das', 'und', 'ist', 'nicht', 'ein', 'eine',
            'mit', 'für', 'auf', 'von', 'zu', 'bei', 'nach', 'vor',
            'ich', 'mein', 'habe', 'kann', 'wird', 'wurde'
        }

        words = text.lower().split()
        keywords = [
            w for w in words
            if len(w) >= 3 and w not in stopwords
        ]

        return list(set(keywords))  # Deduplizieren
```

---

## 🎯 Feature 2: RAG (Retrieval-Augmented Generation)

### Konzept

RAG nutzt **Embeddings** für semantische Ähnlichkeitssuche.

**Vorteile:**
- Findet ähnliche Probleme auch ohne exakte Keywords
- "Windows Update funktioniert nicht" ≈ "Update schlägt fehl"
- Bessere Ergebnisse als reine Keyword-Suche

### Implementation

```python
# ce365/learning/rag.py

from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) für CE365

    Nutzt Sentence Transformers für Embeddings und
    ChromaDB für Vector Search
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        # Embedding Model (Deutsch-fähig!)
        self.embedding_model = SentenceTransformer(model_name)

        # Vector DB
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="data/chromadb"
        ))

        # Collection erstellen/laden
        self.collection = self.chroma_client.get_or_create_collection(
            name="ce365_cases",
            metadata={"hnsw:space": "cosine"}
        )

    def add_case(
        self,
        case_id: str,
        problem_description: str,
        solution: str,
        metadata: dict
    ):
        """Fall zur Vector DB hinzufügen"""
        # Embedding erstellen
        embedding = self.embedding_model.encode(problem_description).tolist()

        # Zu ChromaDB hinzufügen
        self.collection.add(
            ids=[case_id],
            embeddings=[embedding],
            documents=[problem_description],
            metadatas=[{
                "solution": solution,
                **metadata
            }]
        )

    def find_similar(
        self,
        problem_description: str,
        n_results: int = 5,
        os_filter: str = None
    ) -> List[Tuple[str, dict, float]]:
        """
        Ähnliche Fälle finden

        Returns:
            List[(case_id, metadata, similarity_score)]
        """
        # Embedding für Query erstellen
        query_embedding = self.embedding_model.encode(problem_description).tolist()

        # Where-Filter für OS
        where = {"os_type": os_filter} if os_filter else None

        # Suche in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        # Ergebnisse formatieren
        similar_cases = []
        for i in range(len(results['ids'][0])):
            case_id = results['ids'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]

            # Distance zu Similarity (0-1, höher = ähnlicher)
            similarity = 1.0 - distance

            similar_cases.append((case_id, metadata, similarity))

        return similar_cases
```

### Dependencies hinzufügen

```txt
# requirements.txt (erweitern)
sentence-transformers>=2.2.0
chromadb>=0.4.0
```

---

## 🚀 Feature 3: Smart Context Injection

### Konzept

**Problem:** Claude's Context Window ist begrenzt.
**Lösung:** Nur relevante Fälle in System Prompt injizieren.

### Implementation

```python
# ce365/learning/context_builder.py

from typing import List
from ce365.learning.case_library import CaseLibrary, Case
from ce365.learning.rag import RAGSystem

class SmartContextBuilder:
    """
    Baut dynamischen Kontext für System Prompt

    - Findet relevante Fälle
    - Formatiert für Claude
    - Begrenzt Token-Usage
    """

    def __init__(self):
        self.case_library = CaseLibrary()
        self.rag = RAGSystem()

    def build_context(
        self,
        os_type: str,
        problem_description: str,
        error_code: str = None,
        max_cases: int = 3
    ) -> str:
        """
        Relevante Fälle finden und als Kontext formatieren

        Returns:
            Formatierter String für System Prompt
        """
        # Ähnliche Fälle finden (RAG)
        similar_cases = self.rag.find_similar(
            problem_description=problem_description,
            n_results=max_cases,
            os_filter=os_type
        )

        if not similar_cases:
            return ""

        # Kontext formatieren
        context = "\n\n# BEKANNTE FÄLLE (Aus vergangenen Sessions)\n\n"
        context += "Du hast bereits ähnliche Probleme gelöst. Nutze dieses Wissen:\n\n"

        for i, (case_id, metadata, similarity) in enumerate(similar_cases, 1):
            if similarity < 0.7:  # Mindest-Ähnlichkeit 70%
                continue

            context += f"## Fall {i} (Ähnlichkeit: {similarity*100:.0f}%)\n\n"
            context += f"**Problem:** {metadata.get('problem_description', 'N/A')}\n\n"
            context += f"**Root Cause:** {metadata.get('root_cause', 'N/A')}\n\n"
            context += f"**Lösung:** {metadata.get('solution', 'N/A')}\n\n"
            context += f"**Erfolgsquote:** {metadata.get('success_rate', 0)*100:.0f}% ({metadata.get('reuse_count', 0)} Mal verwendet)\n\n"
            context += "---\n\n"

        context += "**Hinweis:** Falls das aktuelle Problem ähnlich ist, kannst du die bewährte Lösung vorschlagen.\n"
        context += "Frage den User: 'Soll ich den bewährten Plan verwenden?'\n\n"

        return context
```

---

## 🔧 Integration in CE365 Agent

### Änderungen in `bot.py`

```python
# ce365/core/bot.py (erweitert)

from ce365.learning.case_library import CaseLibrary, Case
from ce365.learning.context_builder import SmartContextBuilder

class CE365Bot:
    def __init__(self):
        # ... existing code ...

        # Learning System hinzufügen
        self.case_library = CaseLibrary()
        self.context_builder = SmartContextBuilder()
        self.current_case: Optional[Case] = None

    async def process_message(self, user_input: str):
        """Message mit Learning System"""

        # 1. Check ob Problem-Beschreibung (nach Startfragen)
        if self._is_problem_description(user_input):
            # Ähnliche Fälle suchen
            similar_cases = await self._find_similar_cases(user_input)

            if similar_cases:
                # User fragen ob bewährte Lösung
                await self._offer_known_solution(similar_cases[0])

        # 2. Dynamischen Kontext bauen
        if self.state_machine.current_state.value == "audit":
            extra_context = self.context_builder.build_context(
                os_type=self._detected_os,
                problem_description=self._problem_description
            )

            # System Prompt erweitern
            system_prompt = get_system_prompt() + extra_context
        else:
            system_prompt = get_system_prompt()

        # 3. Normal weiter...
        response = self.client.create_message(
            messages=self.session.get_messages(),
            system=system_prompt,  # Mit erweitertem Kontext!
            tools=self.tool_registry.get_tool_definitions(),
        )

        # ... rest of code ...

    async def _find_similar_cases(self, problem_description: str) -> List[Case]:
        """Ähnliche Fälle finden"""
        return self.case_library.find_similar_cases(
            os_type=self._detected_os,
            problem_description=problem_description,
            limit=3
        )

    async def _offer_known_solution(self, case: Case):
        """Bekannte Lösung anbieten"""
        message = f"""
🔍 **Bekanntes Problem erkannt!**

Ich habe ein ähnliches Problem bereits {case.reuse_count} Mal gelöst.
Erfolgsquote: {case.success_rate*100:.0f}%

**Damalige Lösung:**
{case.solution_plan}

**Möchtest du:**
1. Diese bewährte Lösung verwenden (schneller)
2. Vollständigen Audit durchführen (gründlicher)

Bitte antworte mit "1" oder "2".
"""
        self.console.display_assistant_message(message)

    async def complete_session(self, success: bool):
        """
        Session abschließen und Fall speichern
        """
        # Fall für Learning System speichern
        if self.current_case and success:
            case = Case(
                id=None,
                os_type=self._detected_os,
                os_version=self._detected_os_version,
                problem_description=self._problem_description,
                error_codes=self._detected_error_codes,
                root_cause=self._diagnosed_root_cause,
                solution_plan=self.state_machine.repair_plan,
                executed_steps=str(self.state_machine.executed_steps),
                success=success,
                session_id=self.session.session_id,
                created_at=datetime.now()
            )

            case_id = self.case_library.save_case(case)

            self.console.display_success(
                f"✓ Fall gespeichert für zukünftiges Learning (ID: {case_id})"
            )
```

---

## 📈 Feature 4: Playbooks (Automatische Lösungen)

### Konzept

**Playbooks** = Vordefinierte Lösungen für häufige Probleme

```python
# ce365/learning/playbooks.py

from dataclasses import dataclass
from typing import List
import re

@dataclass
class PlaybookStep:
    description: str
    command: str
    risk_level: str  # NIEDRIG, MITTEL, HOCH
    rollback: str

@dataclass
class Playbook:
    id: int
    name: str
    description: str
    os_type: str
    problem_pattern: str  # Regex
    error_code_pattern: str
    steps: List[PlaybookStep]
    success_count: int
    failure_count: int

class PlaybookManager:
    """Verwaltet Playbooks"""

    def __init__(self):
        self.playbooks: List[Playbook] = []
        self._load_default_playbooks()

    def _load_default_playbooks(self):
        """Standard-Playbooks laden"""

        # Windows Update 0x80070002
        self.playbooks.append(Playbook(
            id=1,
            name="Windows Update 0x80070002 Fix",
            description="Behebt häufigen Windows Update Fehler 0x80070002",
            os_type="windows",
            problem_pattern=r"windows\s+update.*fehler|update.*funktioniert\s+nicht",
            error_code_pattern=r"0x80070002",
            steps=[
                PlaybookStep(
                    description="Windows Update Service neustarten",
                    command="net stop wuauserv && net start wuauserv",
                    risk_level="NIEDRIG",
                    rollback="net stop wuauserv && net start wuauserv"
                ),
                PlaybookStep(
                    description="SoftwareDistribution Cache leeren",
                    command="rd /s /q C:\\Windows\\SoftwareDistribution\\Download",
                    risk_level="NIEDRIG",
                    rollback="Automatisch beim nächsten Update"
                )
            ],
            success_count=0,
            failure_count=0
        ))

        # macOS DNS Problem
        self.playbooks.append(Playbook(
            id=2,
            name="macOS DNS Cache leeren",
            description="Behebt DNS-Auflösungsprobleme auf macOS",
            os_type="macos",
            problem_pattern=r"website.*lädt\s+nicht|dns.*problem|internet.*langsam",
            error_code_pattern=None,
            steps=[
                PlaybookStep(
                    description="DNS-Cache leeren",
                    command="sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder",
                    risk_level="NIEDRIG",
                    rollback="Nicht nötig (Cache baut sich neu auf)"
                )
            ],
            success_count=0,
            failure_count=0
        ))

    def find_matching_playbook(
        self,
        os_type: str,
        problem_description: str,
        error_code: str = None
    ) -> List[Playbook]:
        """Passende Playbooks finden"""
        matches = []

        for playbook in self.playbooks:
            # OS-Match
            if playbook.os_type != os_type:
                continue

            # Problem-Pattern-Match
            if re.search(playbook.problem_pattern, problem_description, re.IGNORECASE):
                # Error-Code-Match (wenn vorhanden)
                if error_code and playbook.error_code_pattern:
                    if re.search(playbook.error_code_pattern, error_code):
                        matches.append(playbook)
                else:
                    matches.append(playbook)

        # Nach Erfolgsquote sortieren
        matches.sort(key=lambda p: p.success_count / max(1, p.success_count + p.failure_count), reverse=True)

        return matches
```

---

## 🎨 UI-Integration

### Neue Ausgaben

```python
# ce365/ui/console.py (erweitert)

def display_known_solution(self, case: Case):
    """Bekannte Lösung schön anzeigen"""
    panel_content = f"""
🎯 **BEKANNTES PROBLEM ERKANNT!**

**Problem:** {case.problem_description}
**Root Cause:** {case.root_cause}

**Bewährte Lösung:**
{case.solution_plan}

**Statistik:**
✓ Bereits {case.reuse_count} Mal erfolgreich angewendet
✓ Erfolgsquote: {case.success_rate*100:.0f}%

**Möchtest du diese Lösung verwenden?**
1. Ja, bewährte Lösung (schneller)
2. Nein, vollständiger Audit (gründlicher)
"""

    panel = Panel(
        panel_content,
        title="💡 Smart Learning",
        border_style="green",
        box=box.ROUNDED
    )

    self.console.print(panel)
```

---

## 📊 Analytics & Reporting

```python
# ce365/learning/analytics.py

class LearningAnalytics:
    """Analytics für Learning System"""

    def __init__(self, case_library: CaseLibrary):
        self.case_library = case_library

    def get_statistics(self) -> dict:
        """Learning-Statistiken"""
        conn = sqlite3.connect(self.case_library.db_path)
        cursor = conn.cursor()

        stats = {}

        # Gesamte Fälle
        cursor.execute("SELECT COUNT(*) FROM cases")
        stats['total_cases'] = cursor.fetchone()[0]

        # Erfolgreiche Fälle
        cursor.execute("SELECT COUNT(*) FROM cases WHERE success = TRUE")
        stats['successful_cases'] = cursor.fetchone()[0]

        # Wiederverwendungen
        cursor.execute("SELECT SUM(reuse_count) FROM cases")
        stats['total_reuses'] = cursor.fetchone()[0] or 0

        # Top-Lösungen
        cursor.execute("""
            SELECT problem_description, reuse_count, success_rate
            FROM cases
            WHERE reuse_count > 0
            ORDER BY reuse_count DESC
            LIMIT 5
        """)
        stats['top_solutions'] = cursor.fetchall()

        # OS-Verteilung
        cursor.execute("""
            SELECT os_type, COUNT(*) as count
            FROM cases
            GROUP BY os_type
        """)
        stats['os_distribution'] = dict(cursor.fetchall())

        conn.close()

        return stats

    def print_report(self):
        """Report in Console ausgeben"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("  CE365 LEARNING SYSTEM - REPORT")
        print("="*60)
        print(f"\n📊 Statistiken:")
        print(f"  Gespeicherte Fälle: {stats['total_cases']}")
        print(f"  Erfolgreiche Lösungen: {stats['successful_cases']}")
        print(f"  Wiederverwendungen: {stats['total_reuses']}")

        if stats['top_solutions']:
            print(f"\n🏆 Top 5 Lösungen:")
            for i, (problem, reuse_count, success_rate) in enumerate(stats['top_solutions'], 1):
                print(f"  {i}. {problem[:50]}... ({reuse_count}x, {success_rate*100:.0f}%)")

        if stats['os_distribution']:
            print(f"\n💻 OS-Verteilung:")
            for os_type, count in stats['os_distribution'].items():
                print(f"  {os_type}: {count} Fälle")

        print("\n" + "="*60)
```

---

## 🚀 Implementierungs-Roadmap

### Phase 1: Case Library (1-2 Tage)
- ✅ Datenbank-Schema erstellen
- ✅ `CaseLibrary` Klasse implementieren
- ✅ Integration in `bot.py`
- ✅ Session-Abschluss speichert Fall
- ✅ Einfache Keyword-Suche

### Phase 2: Smart Context (2-3 Tage)
- ✅ `SmartContextBuilder` implementieren
- ✅ Dynamischen Kontext in System Prompt injizieren
- ✅ UI für bekannte Lösungen
- ✅ User kann wählen: Bekannte Lösung oder Full Audit

### Phase 3: RAG System (3-4 Tage)
- ✅ Sentence Transformers integrieren
- ✅ ChromaDB einrichten
- ✅ Embedding-basierte Suche
- ✅ Performance-Tests

### Phase 4: Playbooks (2-3 Tage)
- ✅ Playbook-System implementieren
- ✅ Standard-Playbooks definieren
- ✅ Auto-Detection von passenden Playbooks
- ✅ Success-Tracking

### Phase 5: Analytics (1-2 Tage)
- ✅ Analytics-Dashboard
- ✅ CLI-Command: `ce365 stats`
- ✅ Export-Funktion

**Gesamt: ~2 Wochen**

---

## 💡 Weitere Ideen

### 1. Community Playbooks
- Nutzer können Playbooks teilen
- Rating-System
- Import/Export-Funktion

### 2. Automatisches Feedback
- Nach jeder Lösung: "Hat es funktioniert?"
- Automatisches Success-Tracking
- Self-Improvement

### 3. Multi-Tenancy
- Firmen können eigene Wissensdatenbank haben
- Shared vs. Private Cases
- Export für andere Systeme

### 4. Web-Dashboard
- Visualisierung der gelernten Fälle
- Success-Rate Charts
- Problem-Kategorien

---

**Nächster Schritt:** Soll ich mit der Implementierung beginnen? Ich kann mit **Phase 1 (Case Library)** starten! 🚀
