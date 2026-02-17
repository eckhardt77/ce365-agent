#!/usr/bin/env python3
"""
TechCare Bot - Dokumentation HTML/PDF Generator
Erstellt professionell gestylte HTML und PDF Versionen der Markdown-Dokumente
"""

import markdown
from pathlib import Path
import subprocess
import sys

# Professional CSS Design
CSS_TEMPLATE = """
@page {
    size: A4;
    margin: 2cm;
    @bottom-center {
        content: "TechCare Bot © 2026 Carsten Eckhardt";
        font-size: 9pt;
        color: #666;
    }
    @bottom-right {
        content: "Seite " counter(page) " von " counter(pages);
        font-size: 9pt;
        color: #666;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background: #fff;
}

h1 {
    color: #0066cc;
    border-bottom: 3px solid #0066cc;
    padding-bottom: 10px;
    margin-top: 30px;
    font-size: 2.5em;
    page-break-after: avoid;
}

h2 {
    color: #0088cc;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 8px;
    margin-top: 25px;
    font-size: 2em;
    page-break-after: avoid;
}

h3 {
    color: #00aacc;
    margin-top: 20px;
    font-size: 1.5em;
    page-break-after: avoid;
}

h4 {
    color: #555;
    margin-top: 15px;
    font-size: 1.2em;
}

p {
    margin: 10px 0;
    text-align: justify;
}

ul, ol {
    margin: 10px 0;
    padding-left: 30px;
}

li {
    margin: 5px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    page-break-inside: avoid;
}

th {
    background: linear-gradient(135deg, #0066cc 0%, #0088cc 100%);
    color: white;
    padding: 12px;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 10px 12px;
    border-bottom: 1px solid #e0e0e0;
}

tr:hover {
    background: #f5f5f5;
}

tr:nth-child(even) {
    background: #fafafa;
}

code {
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "Monaco", "Courier New", monospace;
    font-size: 0.9em;
    color: #d63384;
}

pre {
    background: #f8f9fa;
    border-left: 4px solid #0066cc;
    padding: 15px;
    overflow-x: auto;
    border-radius: 4px;
    margin: 15px 0;
    page-break-inside: avoid;
}

pre code {
    background: none;
    padding: 0;
    color: #333;
}

blockquote {
    border-left: 4px solid #0066cc;
    margin: 15px 0;
    padding: 10px 20px;
    background: #f8f9fa;
    font-style: italic;
}

strong {
    color: #0066cc;
    font-weight: 600;
}

a {
    color: #0066cc;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    border: none;
    border-top: 2px solid #e0e0e0;
    margin: 30px 0;
}

.header {
    text-align: center;
    margin-bottom: 40px;
    padding: 30px;
    background: linear-gradient(135deg, #0066cc 0%, #0088cc 100%);
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.header h1 {
    color: white;
    border: none;
    margin: 0;
    font-size: 3em;
}

.header p {
    margin: 10px 0 0 0;
    opacity: 0.9;
    font-size: 1.2em;
}

.emoji {
    font-size: 1.2em;
}

.feature-box {
    background: #f8f9fa;
    border-left: 4px solid #0066cc;
    padding: 15px;
    margin: 15px 0;
    border-radius: 4px;
    page-break-inside: avoid;
}

.warning-box {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 15px;
    margin: 15px 0;
    border-radius: 4px;
}

.success-box {
    background: #d4edda;
    border-left: 4px solid #28a745;
    padding: 15px;
    margin: 15px 0;
    border-radius: 4px;
}

@media print {
    body {
        font-size: 11pt;
    }

    h1 {
        font-size: 24pt;
    }

    h2 {
        font-size: 18pt;
    }

    h3 {
        font-size: 14pt;
    }

    a {
        color: #0066cc;
        text-decoration: none;
    }

    pre, blockquote, table {
        page-break-inside: avoid;
    }
}
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 TechCare Bot</h1>
        <p>{subtitle}</p>
    </div>

    {content}

    <hr>
    <p style="text-align: center; color: #666; font-size: 0.9em;">
        © 2026 Carsten Eckhardt / Eckhardt-Marketing<br>
        <a href="mailto:carsten@eckhardt-marketing.de">carsten@eckhardt-marketing.de</a>
    </p>
</body>
</html>
"""

def convert_markdown_to_html_and_pdf(md_file: Path, output_dir: Path, subtitle: str):
    """
    Konvertiert Markdown zu HTML und PDF

    Args:
        md_file: Pfad zur Markdown-Datei
        output_dir: Output-Verzeichnis
        subtitle: Untertitel für Header
    """
    print(f"📄 Verarbeite {md_file.name}...")

    # Markdown lesen
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Markdown zu HTML konvertieren mit Extensions
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'nl2br',
        'sane_lists'
    ])
    html_content = md.convert(md_content)

    # Vollständiges HTML mit CSS
    title = md_file.stem.replace('_', ' ').title()
    full_html = HTML_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        css=CSS_TEMPLATE,
        content=html_content
    )

    # HTML speichern
    html_path = output_dir / f"{md_file.stem}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"  ✓ HTML: {html_path}")

    # PDF erstellen mit Chrome/Chromium headless
    pdf_path = output_dir / f"{md_file.stem}.pdf"

    try:
        # Versuche Chrome headless zu nutzen
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            'chromium',
            'google-chrome'
        ]

        chrome_cmd = None
        for chrome_path in chrome_paths:
            if Path(chrome_path).exists() or subprocess.run(['which', chrome_path],
                                                           capture_output=True).returncode == 0:
                chrome_cmd = chrome_path
                break

        if chrome_cmd:
            subprocess.run([
                chrome_cmd,
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + str(pdf_path),
                'file://' + str(html_path.absolute())
            ], check=True, capture_output=True)
            print(f"  ✓ PDF:  {pdf_path}")
        else:
            print(f"  ⚠️  Chrome nicht gefunden - PDF manuell erstellen:")
            print(f"     Öffne {html_path} im Browser und drücke Cmd+P -> Als PDF speichern")
            pdf_path = None

    except Exception as e:
        print(f"  ⚠️  PDF-Konvertierung fehlgeschlagen: {e}")
        print(f"     Öffne {html_path} im Browser und drücke Cmd+P -> Als PDF speichern")
        pdf_path = None

    return html_path, pdf_path

def main():
    # Pfade
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "docs"
    output_dir = docs_dir / "export"
    output_dir.mkdir(exist_ok=True)

    print("🚀 TechCare Bot Dokumentation Generator\n")

    # Dokumente konvertieren
    documents = [
        {
            "file": docs_dir / "EDITION_VERGLEICH.md",
            "subtitle": "Community vs. Pro vs. Enterprise - Welche passt zu Ihnen?"
        },
        {
            "file": docs_dir / "PRODUKTBESCHREIBUNG.md",
            "subtitle": "AI-powered IT-Wartungsassistent für Windows & macOS"
        },
        {
            "file": docs_dir / "PROJEKTBESCHREIBUNG.md",
            "subtitle": "Technische Dokumentation & Architektur"
        }
    ]

    results = []
    for doc in documents:
        if doc["file"].exists():
            html_path, pdf_path = convert_markdown_to_html_and_pdf(
                doc["file"],
                output_dir,
                doc["subtitle"]
            )
            results.append({
                "name": doc["file"].stem,
                "html": html_path,
                "pdf": pdf_path
            })
        else:
            print(f"  ⚠️  Datei nicht gefunden: {doc['file']}")

    # Zusammenfassung
    print(f"\n✅ Erfolgreich generiert!")
    print(f"\n📂 Output-Verzeichnis: {output_dir}")
    print("\nGenerierte Dateien:")
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  HTML: {result['html'].name}")
        print(f"  PDF:  {result['pdf'].name}")

if __name__ == "__main__":
    main()
