"""
TechCare Bot - AI-powered IT Maintenance Assistant

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License
"""

import asyncio
import sys
from techcare.core.bot import TechCareBot
from techcare.setup.wizard import run_setup_if_needed


def main():
    """Main Entry Point für TechCare Bot"""
    try:
        # 1. Setup-Wizard (falls .env nicht existiert)
        if not run_setup_if_needed():
            print("\n👋 Setup abgebrochen. Auf Wiedersehen!")
            sys.exit(0)

        # 2. Bot starten
        bot = TechCareBot()
        asyncio.run(bot.run())

    except KeyboardInterrupt:
        print("\n\n👋 Session beendet. Auf Wiedersehen!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Kritischer Fehler: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
