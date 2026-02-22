"""
CE365 Agent - PDF Report Generator

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Generiert professionelle PDF-Reports auf den Desktop.
Nutzt DejaVu Sans (TTF) fuer vollstaendige Unicode-Unterstuetzung.
"""

import re
import sys
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from fpdf import FPDF


# Rich-Markup Tags
_RICH_MARKUP_RE = re.compile(r"\[/?[a-z][a-z _]*\]")

# Emoji-Pattern (Surrogate-Pairs, Variation-Selectors, ZWJ-Sequences)
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # Misc Symbols, Emoticons, etc.
    "\U00002300-\U000023FF"  # Misc Technical (⏱⏰ etc.)
    "\U00002600-\U000026FF"  # Misc Symbols (☀☁ etc.)
    "\U00002702-\U000027B0"  # Dingbats
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000200D"             # ZWJ
    "\U000020E3"             # Combining Enclosing Keycap
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols Extended-A
    "]+",
    flags=re.UNICODE,
)


def _clean_for_pdf(text: str) -> str:
    """Entfernt Rich-Markup und Emojis, behaelt Unicode-Text (Umlaute etc.)"""
    text = _RICH_MARKUP_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    return text.strip()


def _get_font_path(filename: str) -> str:
    """Font-Pfad ermitteln — funktioniert sowohl im Quellcode als auch in PyInstaller-Binary"""
    if getattr(sys, "frozen", False):
        # PyInstaller: Daten liegen in _MEIPASS
        base = Path(sys._MEIPASS) / "ce365" / "assets" / filename
        if base.exists():
            return str(base)
    # Quellcode: ce365/tools/audit/pdf_report.py -> 3x parent = ce365/ -> assets/
    font_path = Path(__file__).resolve().parent.parent.parent / "assets" / filename
    return str(font_path)


from ce365.tools.base import AuditTool


class CE365PDF(FPDF):
    """Angepasste FPDF-Klasse mit CE365 Header/Footer und DejaVu-Font"""

    def __init__(self, technician: str = "", company: str = ""):
        super().__init__()
        self.technician = technician
        self.company = company
        # DejaVu Sans registrieren (Unicode-faehig)
        dejavu_regular = _get_font_path("DejaVuSans.ttf")
        dejavu_bold = _get_font_path("DejaVuSans-Bold.ttf")
        self.add_font("DejaVu", "", dejavu_regular, uni=True)
        self.add_font("DejaVu", "B", dejavu_bold, uni=True)

    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, "CE365 Agent", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, "AI-powered IT-Wartungsassistent", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 150, 200)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generiert von CE365 Agent | Seite {self.page_no()}/{{nb}}", align="C")


def _get_desktop_path() -> Path:
    """Desktop-Pfad plattformuebergreifend ermitteln"""
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return desktop
    return Path.home()


def generate_pdf_report(
    report_data: Dict[str, Any],
    technician: str = "",
    company: str = "",
    customer_name: str = "",
    ticket_id: str = "",
    output_path: Optional[Path] = None,
) -> str:
    """
    Generiert professionelles PDF-Report.

    Args:
        report_data: Dict mit Keys:
            - system_info: str (System-Informationen)
            - sections: list of {"title": str, "content": str} (flexible Sektionen)
            - findings: list of {"priority": str, "title": str, "detail": str}
            - repairs: str
            - recommendations: str
            - raw_analysis: str
        technician: Techniker-Name
        company: Firmenname
        output_path: Optionaler Pfad (Default: Desktop)

    Returns:
        Pfad zur gespeicherten PDF
    """
    hostname = platform.node()
    datum = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if output_path is None:
        filename = f"CE365-Report-{hostname}-{datum}.pdf"
        output_path = _get_desktop_path() / filename

    pdf = CE365PDF(technician=technician, company=company)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # -- Report-Info Block (zweispaltig) --
    pdf.set_font("DejaVu", "", 10)

    # Rechte Spalte: Techniker, Firma, Kunde, Ticket
    right_lines = []
    if company:
        right_lines.append(f"Firma: {company}")
    if technician:
        right_lines.append(f"Techniker: {technician}")
    if customer_name:
        right_lines.append(f"Kunde: {customer_name}")
    if ticket_id:
        right_lines.append(f"Ticket-ID: {ticket_id}")
    right_lines.append(f"Datum: {timestamp}")

    # Linke Spalte: Hardware-Info
    left_lines = [f"Hostname: {hostname}"]
    try:
        from ce365.tools.audit.system_info import get_hardware_info
        hw = get_hardware_info()
        if hw.get("os_name"):
            left_lines.append(f"System: {hw['os_name']}")
        if hw.get("manufacturer") or hw.get("model"):
            device = f"{hw.get('manufacturer', '')} {hw.get('model', '')}".strip()
            left_lines.append(f"Geraet: {device}")
        if hw.get("cpu_name"):
            left_lines.append(f"CPU: {hw['cpu_name']}")
        if hw.get("gpu"):
            left_lines.append(f"GPU: {hw['gpu']}")
        left_lines.append(f"RAM: {hw.get('ram_total_gb', '?')} GB")
        if hw.get("serial"):
            left_lines.append(f"Seriennummer: {hw['serial']}")
    except Exception:
        pass

    # Beide Spalten nebeneinander rendern
    col_width = 90
    start_y = pdf.get_y()
    max_rows = max(len(left_lines), len(right_lines))
    for i in range(max_rows):
        # Linke Spalte
        if i < len(left_lines):
            pdf.set_xy(10, start_y + i * 6)
            pdf.cell(col_width, 6, _clean_for_pdf(left_lines[i]))
        # Rechte Spalte
        if i < len(right_lines):
            pdf.set_xy(10 + col_width, start_y + i * 6)
            pdf.cell(col_width, 6, _clean_for_pdf(right_lines[i]))
    pdf.set_y(start_y + max_rows * 6 + 5)

    # -- System-Informationen --
    system_info = report_data.get("system_info", "")
    if system_info:
        _add_section(pdf, "System-Informationen", system_info)

    # -- Flexible Sections (von Audit-Tools) --
    sections: List[Dict[str, str]] = report_data.get("sections", [])
    for section in sections:
        title = section.get("title", "")
        content = section.get("content", "")
        if title and content:
            _add_section(pdf, title, content)

    # -- Findings --
    findings = report_data.get("findings", [])
    if findings:
        pdf.set_font("DejaVu", "B", 13)
        pdf.cell(0, 10, "Analyse-Ergebnisse", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        for finding in findings:
            priority = finding.get("priority", "info")
            title = finding.get("title", "")
            detail = finding.get("detail", "")

            # Farbcodierung
            if priority == "critical":
                pdf.set_text_color(200, 0, 0)
                prefix = "[KRITISCH]"
            elif priority == "warning":
                pdf.set_text_color(200, 150, 0)
                prefix = "[WARNUNG]"
            else:
                pdf.set_text_color(0, 150, 0)
                prefix = "[OK]"

            pdf.set_font("DejaVu", "B", 10)
            pdf.cell(0, 7, _clean_for_pdf(f"{prefix} {title}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

            if detail:
                pdf.set_font("DejaVu", "", 9)
                pdf.multi_cell(0, 5, _clean_for_pdf(detail), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    # -- Durchgefuehrte Reparaturen --
    repairs = report_data.get("repairs", "")
    if repairs:
        _add_section(pdf, "Durchgefuehrte Reparaturen", repairs)

    # -- Empfehlungen --
    recommendations = report_data.get("recommendations", "")
    if recommendations:
        _add_section(pdf, "Empfehlungen", recommendations)

    # -- Raw Scan Data (falls vorhanden) --
    raw_analysis = report_data.get("raw_analysis", "")
    if raw_analysis:
        _add_section(pdf, "Detaillierte Analyse", raw_analysis)

    # PDF speichern
    pdf.output(str(output_path))
    return str(output_path)


def _add_section(pdf: FPDF, title: str, content: str):
    """Section mit Titel und Inhalt zum PDF hinzufuegen"""
    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, _clean_for_pdf(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 9)

    clean = _clean_for_pdf(content)

    for line in clean.split("\n"):
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue
        pdf.multi_cell(0, 5, stripped, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)


class SaveReportPDFTool(AuditTool):
    """Tool fuer Claude: PDF-Report auf Desktop speichern"""

    @property
    def name(self) -> str:
        return "save_report_pdf"

    @property
    def description(self) -> str:
        return (
            "Speichert einen System-Report als PDF auf den Desktop des Kunden. "
            "Nutze dies nach einer System-Analyse oder auf Wunsch des Technikers. "
            "Uebergib die Analyse-Ergebnisse als Text."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "analysis_text": {
                    "type": "string",
                    "description": "Die vollstaendige Analyse / Findings als Text",
                },
                "system_info": {
                    "type": "string",
                    "description": "System-Informationen (OS, CPU, RAM, Disk)",
                    "default": "",
                },
                "recommendations": {
                    "type": "string",
                    "description": "Empfehlungen fuer den Kunden",
                    "default": "",
                },
            },
            "required": ["analysis_text"],
        }

    async def execute(self, **kwargs) -> str:
        analysis_text = kwargs.get("analysis_text", "")
        system_info = kwargs.get("system_info", "")
        recommendations = kwargs.get("recommendations", "")

        try:
            from ce365.config.settings import get_settings
            settings = get_settings()
            technician = settings.technician_name or ""
            company = settings.company or ""
        except Exception:
            technician = ""
            company = ""

        report_data = {
            "system_info": system_info,
            "raw_analysis": analysis_text,
            "recommendations": recommendations,
        }

        try:
            path = generate_pdf_report(
                report_data=report_data,
                technician=technician,
                company=company,
            )
            return f"PDF-Report gespeichert: {path}"
        except Exception as e:
            return f"PDF-Fehler: {e}"
