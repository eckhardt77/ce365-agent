#!/bin/bash
# ============================================================================
# CE365 Agent - Installer
# ============================================================================
# Installiert CE365 Agent als lokales CLI-Tool.
# Kein Docker, kein Server — nur Python + pip.
# ============================================================================

set -e

echo ""
echo "🔧 CE365 Agent - Installer"
echo "=========================="
echo ""

# 1. Python-Version prüfen
echo "📋 Prüfe Python-Version..."

PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON=$cmd
            echo "   ✓ $cmd ($version)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "   ❌ Python >= 3.10 erforderlich!"
    echo "   Installiere Python: https://www.python.org/downloads/"
    exit 1
fi

# 2. Virtual Environment erstellen
echo ""
echo "📦 Erstelle Virtual Environment..."

if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "   ✓ venv erstellt"
else
    echo "   ✓ venv existiert bereits"
fi

# Aktivieren
source venv/bin/activate
echo "   ✓ venv aktiviert"

# 3. Dependencies installieren
echo ""
echo "📥 Installiere Dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "   ✓ Dependencies installiert"

# 4. Setup-Wizard starten
echo ""
echo "🧙 Starte Setup-Wizard..."
echo ""
python -m ce365

echo ""
echo "============================================"
echo "✅ CE365 Agent erfolgreich installiert!"
echo ""
echo "Starten mit:"
echo "   source venv/bin/activate"
echo "   python -m ce365"
echo ""
echo "Oder direkt:"
echo "   ./venv/bin/python -m ce365"
echo "============================================"
