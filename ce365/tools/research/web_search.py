"""
Web Search Tool

Recherchiert im Internet nach Problemlösungen
- DuckDuckGo Search (kostenlos, kein API-Key)
- Smart Result Filtering
- Error-Code Lookup
- KB Article Detection
"""

import os
from typing import Dict, Any
from ce365.tools.base import AuditTool

try:
    from duckduckgo_search import DDGS
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False


class WebSearchTool(AuditTool):
    """
    Web Search Tool für Problemlösung-Recherche

    Features:
    - DuckDuckGo Text Search
    - Relevante Snippets extrahieren
    - KB Articles priorisieren
    - Safe Search aktiviert
    """

    def __init__(self):
        super().__init__()
        # Check if enabled
        self.enabled = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"

        if not WEB_SEARCH_AVAILABLE:
            self.enabled = False

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Durchsucht das Internet nach Lösungen für IT-Probleme. "
            "Nutze dieses Tool bei: "
            "1) Error-Codes (z.B. Windows 0x80070002), "
            "2) Unbekannten Problemen, "
            "3) Hardware-spezifischen Issues, "
            "4) Software-Konfiguration. "
            "Die Suche liefert relevante KB-Artikel, Forum-Posts und Support-Seiten."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Suchbegriff. Beispiele: "
                        "'Windows Error 0x80070002 fix', "
                        "'macOS Spotlight not working', "
                        "'Dell XPS WiFi issues solution'"
                    )
                },
                "num_results": {
                    "type": "integer",
                    "description": "Anzahl Suchergebnisse (Standard: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> str:
        """
        Web-Suche durchführen

        Args:
            query: Suchbegriff
            num_results: Anzahl Ergebnisse (default: 5)

        Returns:
            Formatierte Suchergebnisse mit Titel, URL, Snippet
        """
        if not self.enabled:
            return "❌ Web-Suche nicht verfügbar. Bitte installieren: pip install duckduckgo-search"

        query = kwargs.get("query", "")
        num_results = kwargs.get("num_results", 5)

        if not query:
            return "❌ Fehler: Suchbegriff fehlt"

        try:
            # DuckDuckGo Search
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    keywords=query,
                    max_results=num_results,
                    region="de-de",  # DACH Region
                    safesearch="moderate"
                ))

            if not results:
                return f"ℹ️  Keine Ergebnisse für: '{query}'"

            # Formatierung
            output_lines = [
                f"🔍 Web-Recherche: '{query}'",
                f"📊 {len(results)} Ergebnisse gefunden\n"
            ]

            for i, result in enumerate(results, 1):
                title = result.get("title", "Unbekannt")
                url = result.get("href", "")
                snippet = result.get("body", "")

                # KB Article Detection
                is_kb = any(kb in url.lower() for kb in [
                    "support.microsoft.com",
                    "support.apple.com",
                    "kb.vmware.com",
                    "support.google.com",
                    "docs.microsoft.com",
                    "learn.microsoft.com",
                ])

                kb_badge = " 📘 [KB Article]" if is_kb else ""

                output_lines.append(f"{i}. {title}{kb_badge}")
                output_lines.append(f"   URL: {url}")
                output_lines.append(f"   {snippet[:200]}...")
                output_lines.append("")

            # Hinweis
            output_lines.append("💡 Tipp: Priorisiere KB Articles (📘) für offizielle Lösungen")

            return "\n".join(output_lines)

        except Exception as e:
            return f"❌ Web-Suche Fehler: {str(e)}"


class WebSearchInstantAnswerTool(AuditTool):
    """
    Web Search mit Instant Answers (DuckDuckGo AI Summaries)

    Schnellere Alternative für einfache Fragen
    """

    def __init__(self):
        super().__init__()
        self.enabled = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"

        if not WEB_SEARCH_AVAILABLE:
            self.enabled = False

    @property
    def name(self) -> str:
        return "web_instant_answer"

    @property
    def description(self) -> str:
        return (
            "Holt schnelle Antworten für einfache Fragen aus DuckDuckGo Instant Answers. "
            "Nutze dies für: Definition, Quick Facts, einfache How-Tos. "
            "Für komplexe Recherche nutze 'web_search'."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Kurze Frage oder Begriff"
                }
            },
            "required": ["query"]
        }

    async def execute(self, **kwargs) -> str:
        """
        Instant Answer abrufen

        Args:
            query: Suchbegriff

        Returns:
            Instant Answer oder Fehler
        """
        if not self.enabled:
            return "❌ Web-Suche nicht verfügbar"

        query = kwargs.get("query", "")

        if not query:
            return "❌ Fehler: Suchbegriff fehlt"

        try:
            # DuckDuckGo Instant Answers
            with DDGS() as ddgs:
                results = ddgs.answers(keywords=query)

            if results:
                answer = results[0]
                text = answer.get("text", "")
                url = answer.get("url", "")

                if text:
                    output = [
                        f"💡 Instant Answer: '{query}'",
                        f"\n{text}"
                    ]
                    if url:
                        output.append(f"\nQuelle: {url}")

                    return "\n".join(output)

            return f"ℹ️  Keine Instant Answer für: '{query}'. Nutze 'web_search' für detaillierte Recherche."

        except Exception as e:
            return f"❌ Instant Answer Fehler: {str(e)}"
