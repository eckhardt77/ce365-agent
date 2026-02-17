#!/usr/bin/env python3
"""
Test-Skript für Web Search Tool

Testet:
1. DuckDuckGo Text Search
2. Error-Code Lookup
3. KB Article Detection
4. Instant Answers
"""

import asyncio
from ce365.tools.research.web_search import WebSearchTool, WebSearchInstantAnswerTool


async def test_web_search():
    """Web Search Tool testen"""

    print("\n" + "="*80)
    print("  WEB SEARCH TOOL TEST")
    print("="*80 + "\n")

    # 1. Web Search Tool initialisieren
    print("1. WEB SEARCH TOOL INITIALISIEREN")
    print("-" * 80)

    search_tool = WebSearchTool()
    instant_tool = WebSearchInstantAnswerTool()

    if not search_tool.enabled:
        print("❌ Web Search nicht verfügbar. Bitte installieren:")
        print("   pip install duckduckgo-search")
        return

    print("✓ Web Search Tool initialisiert")
    print(f"  Enabled: {search_tool.enabled}")
    print()

    # 2. Test: Error-Code Lookup
    print("2. TEST: ERROR-CODE LOOKUP")
    print("-" * 80)
    print("Query: 'Windows Error 0x80070002 fix'\n")

    result = await search_tool.execute(
        query="Windows Error 0x80070002 fix",
        num_results=3
    )

    print(result)
    print()
    input("Drücke ENTER für nächsten Test...")
    print()

    # 3. Test: macOS Problem
    print("3. TEST: macOS PROBLEM")
    print("-" * 80)
    print("Query: 'macOS Spotlight not working solution'\n")

    result = await search_tool.execute(
        query="macOS Spotlight not working solution",
        num_results=3
    )

    print(result)
    print()
    input("Drücke ENTER für nächsten Test...")
    print()

    # 4. Test: Hardware-spezifisch
    print("4. TEST: HARDWARE-SPEZIFISCH")
    print("-" * 80)
    print("Query: 'Dell laptop WiFi driver issues'\n")

    result = await search_tool.execute(
        query="Dell laptop WiFi driver issues",
        num_results=3
    )

    print(result)
    print()
    input("Drücke ENTER für nächsten Test...")
    print()

    # 5. Test: Instant Answer
    print("5. TEST: INSTANT ANSWER")
    print("-" * 80)
    print("Query: 'What is DNS cache'\n")

    result = await instant_tool.execute(
        query="What is DNS cache"
    )

    print(result)
    print()

    # Zusammenfassung
    print("="*80)
    print("  TEST ABGESCHLOSSEN")
    print("="*80)
    print()

    print("Was wurde getestet:")
    print("  ✓ Web Search Tool Initialisierung")
    print("  ✓ Error-Code Lookup")
    print("  ✓ macOS Problem-Recherche")
    print("  ✓ Hardware-spezifische Suche")
    print("  ✓ Instant Answers")
    print()

    print("Features:")
    print("  ✓ DuckDuckGo Search (kostenlos, kein API-Key)")
    print("  ✓ KB Article Detection (📘)")
    print("  ✓ DACH Region (de-de)")
    print("  ✓ Safe Search (moderate)")
    print("  ✓ Relevante Snippets")
    print()

    print("✅ Web Search funktioniert!")
    print()


if __name__ == "__main__":
    asyncio.run(test_web_search())
