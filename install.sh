#!/bin/bash
#
# TechCare Bot - One-Command Installation Script
#
# Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
# Licensed under MIT License
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/your-repo/techcare-bot/main/install.sh | bash
#   or locally: bash install.sh

set -e  # Exit on error

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🔧 TechCare Bot - Installation                               ║"
echo "║                                                                ║"
echo "║   AI-powered IT-Wartungsassistent                              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Prüfe Python-Version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nicht gefunden!"
    echo "   Bitte installiere Python 3.9+ von https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION gefunden"

# Check minimum Python version (3.9)
REQUIRED_VERSION="3.9"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.9+ erforderlich, aber $PYTHON_VERSION gefunden"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Erstelle Virtual Environment..."
if [ -d "venv" ]; then
    echo "⚠️  venv existiert bereits, überspringe..."
else
    python3 -m venv venv
    echo "✓ Virtual Environment erstellt"
fi

# Activate venv
echo ""
echo "🔌 Aktiviere Virtual Environment..."
source venv/bin/activate
echo "✓ Virtual Environment aktiviert"

# Upgrade pip
echo ""
echo "⬆️  Aktualisiere pip..."
pip install --upgrade pip -q
echo "✓ pip aktualisiert"

# Install dependencies
echo ""
echo "📚 Installiere Dependencies..."
echo "   (Das kann 2-3 Minuten dauern...)"
pip install -r requirements.txt -q
echo "✓ Dependencies installiert"

# Install Spacy German model
echo ""
echo "🇩🇪 Installiere deutsches Sprachmodell (für PII Detection)..."
python -m spacy download de_core_news_md -q
echo "✓ Sprachmodell installiert"

# Install TechCare Bot
echo ""
echo "🤖 Installiere TechCare Bot..."
pip install -e . -q
echo "✓ TechCare Bot installiert"

# Success message
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   ✅ Installation erfolgreich!                                 ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Starten mit:"
echo ""
echo "   source venv/bin/activate  # (falls nicht bereits aktiviert)"
echo "   techcare"
echo ""
echo "Beim ersten Start führt dich ein Setup-Assistent durch die"
echo "Konfiguration (API Key, etc.)."
echo ""
echo "📖 Dokumentation: docs/INSTALLATION.md"
echo "❓ Hilfe: https://github.com/your-repo/techcare-bot/issues"
echo ""
