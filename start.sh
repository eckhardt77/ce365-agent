#!/bin/bash
# TechCare Bot - One-Command Starter
# Usage: ./start.sh [args] or techcare [args]

# Finde den echten Pfad (auch wenn als Symlink aufgerufen)
SCRIPT_PATH="$0"
# Resolve symlinks
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    # Wenn relativer Link, dann von SCRIPT_DIR aus auflösen
    [[ "$SCRIPT_PATH" != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# Aktiviere Virtual Environment aus dem echten TechCare-Verzeichnis
source "$SCRIPT_DIR/venv/bin/activate"

# Starte TechCare mit allen übergebenen Argumenten
techcare "$@"
