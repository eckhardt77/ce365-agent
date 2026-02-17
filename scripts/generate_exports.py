#!/usr/bin/env python3
"""
TechCare Bot - Documentation Export Generator

Converts Markdown files to HTML and PDF with professional styling.

Usage:
    python scripts/generate_exports.py
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import datetime


# Pfade
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
EXPORT_DIR = DOCS_DIR / "export"

# Zu exportierende Dateien
FILES_TO_EXPORT = [
    {
        "source": DOCS_DIR / "PRODUKTBESCHREIBUNG.md",
        "name": "PRODUKTBESCHREIBUNG"
    },
    {
        "source": DOCS_DIR / "EDITION_VERGLEICH.md",
        "name": "EDITION_VERGLEICH"
    },
    {
        "source": PROJECT_ROOT / "README_DE.md",
        "name": "README_DE"
    }
]

# CSS Styling für HTML/PDF
CSS_STYLE = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #24292e;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    font-size: 11pt;
}

h1 {
    color: #0366d6;
    border-bottom: 3px solid #0366d6;
    padding-bottom: 0.3em;
    font-size: 24pt;
    margin-top: 1em;
}

h2 {
    color: #0366d6;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
    font-size: 18pt;
    margin-top: 1.5em;
}

h3 {
    color: #24292e;
    font-size: 14pt;
    margin-top: 1.2em;
}

h4 {
    color: #586069;
    font-size: 12pt;
    margin-top: 1em;
}

a {
    color: #0366d6;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

code {
    background-color: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 9pt;
}

pre {
    background-color: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.4;
}

pre code {
    background-color: transparent;
    padding: 0;
}

blockquote {
    border-left: 4px solid #dfe2e5;
    padding-left: 1em;
    color: #6a737d;
    margin-left: 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 10pt;
}

th, td {
    border: 1px solid #dfe2e5;
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #f6f8fa;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

ul, ol {
    padding-left: 2em;
}

li {
    margin: 0.5em 0;
}

hr {
    border: none;
    border-top: 2px solid #eaecef;
    margin: 2em 0;
}

img {
    max-width: 100%;
    height: auto;
}

.header {
    text-align: center;
    color: #586069;
    font-size: 9pt;
    margin-bottom: 2em;
    padding-bottom: 1em;
    border-bottom: 1px solid #eaecef;
}

.footer {
    text-align: center;
    color: #586069;
    font-size: 9pt;
    margin-top: 3em;
    padding-top: 1em;
    border-top: 1px solid #eaecef;
}

/* Emoji-Unterstützung */
.emoji {
    font-family: "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    background-color: #0366d6;
    color: white;
    font-size: 9pt;
    font-weight: 600;
    margin-right: 5px;
}

/* Print-spezifisch */
@media print {
    body {
        font-size: 10pt;
    }

    h1 {
        page-break-before: auto;
        page-break-after: avoid;
    }

    h2, h3, h4 {
        page-break-after: avoid;
    }

    pre, table {
        page-break-inside: avoid;
    }
}
"""


def ensure_export_dir():
    """Erstellt Export-Verzeichnis falls nicht vorhanden"""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Export-Verzeichnis: {EXPORT_DIR}")


def markdown_to_html(md_content: str, title: str) -> str:
    """
    Konvertiert Markdown zu HTML mit Styling

    Args:
        md_content: Markdown-Inhalt
        title: Dokument-Titel

    Returns:
        Vollständiges HTML-Dokument
    """
    # Markdown Extensions
    md = markdown.Markdown(extensions=[
        'extra',          # Tabellen, Fenced Code Blocks, etc.
        'codehilite',     # Syntax Highlighting
        'toc',            # Table of Contents
        'nl2br',          # Newline to <br>
        'sane_lists',     # Bessere Listen
    ])

    # Konvertiere Markdown
    html_content = md.convert(md_content)

    # Erstelle vollständiges HTML-Dokument
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    full_html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - TechCare Bot v2.0.0</title>
    <style>
        {CSS_STYLE}
    </style>
</head>
<body>
    <div class="header">
        <strong>TechCare Bot v2.0.0</strong><br>
        {title}<br>
        Generiert: {now}
    </div>

    {html_content}

    <div class="footer">
        <strong>TechCare Bot</strong> - AI-powered IT Maintenance Assistant<br>
        Copyright © 2026 Carsten Eckhardt / Eckhardt-Marketing<br>
        <a href="https://techcare.eckhardt-marketing.de">techcare.eckhardt-marketing.de</a>
    </div>
</body>
</html>
"""

    return full_html


def html_to_pdf(html_content: str, output_path: Path):
    """
    Konvertiert HTML zu PDF mit WeasyPrint

    Args:
        html_content: HTML-Inhalt
        output_path: Ausgabe-Pfad für PDF
    """
    # WeasyPrint: HTML → PDF
    HTML(string=html_content).write_pdf(
        output_path,
        stylesheets=[CSS(string=CSS_STYLE)]
    )


def export_file(file_info: dict):
    """
    Exportiert eine Markdown-Datei zu HTML und PDF

    Args:
        file_info: Dict mit 'source' und 'name'
    """
    source = file_info["source"]
    name = file_info["name"]

    if not source.exists():
        print(f"⚠️  Überspringe {name} (Datei nicht gefunden)")
        return

    print(f"\n📄 Exportiere {name}...")

    try:
        # Markdown lesen
        md_content = source.read_text(encoding='utf-8')

        # HTML generieren
        html_content = markdown_to_html(md_content, name)
        html_path = EXPORT_DIR / f"{name}.html"
        html_path.write_text(html_content, encoding='utf-8')
        print(f"   ✅ HTML: {html_path.name}")

        # PDF generieren
        pdf_path = EXPORT_DIR / f"{name}.pdf"
        html_to_pdf(html_content, pdf_path)
        print(f"   ✅ PDF:  {pdf_path.name}")

    except Exception as e:
        print(f"   ❌ Fehler: {str(e)}")


def main():
    """Main Entry Point"""
    print("=" * 60)
    print("🔧 TechCare Bot - Documentation Export Generator")
    print("=" * 60)
    print()

    # Export-Verzeichnis erstellen
    ensure_export_dir()

    # Dateien exportieren
    for file_info in FILES_TO_EXPORT:
        export_file(file_info)

    print()
    print("=" * 60)
    print("✅ Export abgeschlossen!")
    print("=" * 60)
    print()
    print(f"📁 Ausgabe-Verzeichnis: {EXPORT_DIR}")
    print()
    print("Generierte Dateien:")
    for file_info in FILES_TO_EXPORT:
        name = file_info["name"]
        print(f"  • {name}.html")
        print(f"  • {name}.pdf")
    print()


if __name__ == "__main__":
    main()
