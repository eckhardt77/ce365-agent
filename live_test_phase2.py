#!/usr/bin/env python3
"""
CE365 Agent - Live API Test Phase 2
Testet Audit-Phase mit Tool Use
"""

import asyncio
from ce365.core.bot import CE365Bot

async def live_test_phase2():
    """Test Phase 2: Audit mit Tool Use"""

    print("\n" + "="*80)
    print("  LIVE API TEST - PHASE 2: AUDIT")
    print("="*80 + "\n")

    try:
        bot = CE365Bot()
        print(f"✓ Bot initialisiert (Session: {bot.session.session_id})\n")

        # Phase 1: Startfragen
        print("PHASE 1: Startfragen")
        print("-" * 80)
        await bot.process_message("Neuer Fall")
        print()

        # Phase 2: Antworten auf Startfragen
        print("\nPHASE 2: Startfragen beantworten")
        print("-" * 80)
        print("Sende: Backup-Antwort\n")

        user_answer = """Ja, Time Machine Backup vorhanden.
macOS Sequoia 15.
Problem: WLAN verbunden, aber Websites laden nicht.
Bereits versucht: Neustart, aber Problem besteht."""

        await bot.process_message(user_answer)
        print()

        # Token Usage
        usage = bot.client.get_token_usage()
        print("\nTOKEN USAGE (gesamt):")
        print(f"  Input:  {usage['input_tokens']}")
        print(f"  Output: {usage['output_tokens']}")
        print(f"  Total:  {usage['total_tokens']}")
        print()

        # State & Tool Check
        print("STATE & TOOL CHECK:")
        print(f"  Workflow State: {bot.state_machine.current_state.value}")
        print(f"  Session Messages: {len(bot.session.messages)}")
        print()

        print("="*80)
        print("  PHASE 2 TEST ABGESCHLOSSEN")
        print("="*80)
        print()
        print("ERWARTETES VERHALTEN:")
        print("  ✓ CE365 sollte Backup bestätigen")
        print("  ✓ CE365 sollte macOS erkennen")
        print("  ✓ CE365 sollte AUDIT-KIT macOS verwenden")
        print("  ✓ CE365 sollte get_system_info Tool aufrufen")
        print("  ✓ CE365 sollte nach Output fragen")
        print()

    except Exception as e:
        print(f"\n❌ FEHLER: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(live_test_phase2())
    exit(0 if success else 1)
