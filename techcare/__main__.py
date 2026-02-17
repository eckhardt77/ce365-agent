"""
TechCare Bot - AI-powered IT Maintenance Assistant

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License
"""

import asyncio
import sys
from techcare.core.bot import TechCareBot


def main():
    """Main Entry Point für TechCare Bot"""
    try:
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
