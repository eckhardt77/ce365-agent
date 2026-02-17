#!/usr/bin/env python3
"""
CE365 Agent - Live API Test

Testet den Bot mit echtem Anthropic API Key
"""

import asyncio
from ce365.core.bot import CE365Bot
from ce365.config.system_prompt import get_system_prompt

async def live_test():
    """Live-Test mit echtem API Key"""

    print("\n" + "="*80)
    print("  LIVE API TEST - CE365 Agent")
    print("="*80 + "\n")

    try:
        # Bot initialisieren
        print("Initialisiere CE365 Agent...")
        bot = CE365Bot()
        print(f"✓ Bot initialisiert (Session: {bot.session.session_id})")
        print(f"✓ Model: {bot.client.model}")
        print(f"✓ Tools: {len(bot.tool_registry)}")
        print()

        # Test 1: System Prompt Check
        print("TEST 1: System Prompt")
        print("-" * 80)
        system_prompt = get_system_prompt()

        checks = [
            "STARTFRAGEN",
            "Backup",
            "ALLOWLIST",
            "BLOCKLIST",
            "EINZELSCHRITT"
        ]

        for check in checks:
            if check in system_prompt:
                print(f"  ✓ {check} vorhanden")
            else:
                print(f"  ✗ {check} FEHLT!")

        print()

        # Test 2: Erste Interaktion (Startfragen)
        print("TEST 2: Erste Interaktion")
        print("-" * 80)
        print("Sende: 'Neuer Fall'\n")

        # Simuliere User-Input
        await bot.process_message("Neuer Fall")

        print()
        print("-" * 80)
        print("✓ Erste Interaktion abgeschlossen")
        print()

        # Token Usage
        usage = bot.client.get_token_usage()
        print("TOKEN USAGE:")
        print(f"  Input:  {usage['input_tokens']}")
        print(f"  Output: {usage['output_tokens']}")
        print(f"  Total:  {usage['total_tokens']}")
        print()

        # State Check
        print("STATE CHECK:")
        print(f"  Workflow State: {bot.state_machine.current_state.value}")
        print(f"  Session Messages: {len(bot.session.messages)}")
        print()

        print("="*80)
        print("  LIVE TEST ABGESCHLOSSEN")
        print("="*80)
        print()
        print("ERWARTETES VERHALTEN:")
        print("  ✓ CE365 sollte STARTFRAGEN stellen")
        print("  ✓ Erste Frage sollte BACKUP-CHECK sein")
        print("  ✓ Alle Antworten sollten auf DEUTSCH sein")
        print()
        print(f"Changelog: {bot.changelog.log_path}")
        print()

    except Exception as e:
        print(f"\n❌ FEHLER: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(live_test())
    exit(0 if success else 1)
