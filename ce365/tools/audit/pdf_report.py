"""
CE365 Agent - PDF Report Generator

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Generiert professionelle PDF-Reports auf den Desktop.
"""

import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from fpdf import FPDF

from ce365.tools.base import AuditTool


class CE365PDF(FPDF):
    """Angepasste FPDF-Klasse mit CE365 Header/Footer"""

    def __init__(self, technician: str = "", company: str = ""):
        super().__init__()
        self.technician = technician
        self.company = company

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "CE365 Agent", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, "AI-powered IT-Wartungsassistent", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 150, 200)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
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
    output_path: Optional[Path] = None,
) -> str:
    """
    Generiert professionelles PDF-Report.

    Args:
        report_data: Dict mit Sections (system_info, findings, repairs, recommendations)
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

    # -- Report-Info Block --
    pdf.set_font("Helvetica", "", 10)
    info_lines = [
        f"Datum: {timestamp}",
        f"Hostname: {hostname}",
    ]
    if technician:
        info_lines.append(f"Techniker: {technician}")
    if company:
        info_lines.append(f"Firma: {company}")

    # Hardware-Kurzinfo
    try:
        from ce365.tools.audit.system_info import get_hardware_info
        hw = get_hardware_info()
        if hw.get("os_name"):
            info_lines.append(f"System: {hw['os_name']}")
        if hw.get("manufacturer") or hw.get("model"):
            device = f"{hw.get('manufacturer', '')} {hw.get('model', '')}".strip()
            info_lines.append(f"Geraet: {device}")
        if hw.get("cpu_name"):
            info_lines.append(f"CPU: {hw['cpu_name']}")
        if hw.get("gpu"):
            info_lines.append(f"GPU: {hw['gpu']}")
        info_lines.append(f"RAM: {hw.get('ram_total_gb', '?')} GB")
        if hw.get("serial"):
            info_lines.append(f"Seriennummer: {hw['serial']}")
    except Exception:
        pass

    for line in info_lines:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # -- System-Informationen --
    system_info = report_data.get("system_info", "")
    if system_info:
        _add_section(pdf, "System-Informationen", system_info)

    # -- Findings --
    findings = report_data.get("findings", [])
    if findings:
        pdf.set_font("Helvetica", "B", 13)
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

            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, f"{prefix} {title}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

            if detail:
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 5, detail)
            pdf.ln(3)

    # -- Durchgefuehrte Reparaturen --
    repairs = report_data.get("repairs", "")
    if repairs:
        _add_section(pdf, "Durchgeführte Reparaturen", repairs)

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
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)

    # Emojis und Rich-Markup entfernen fuer PDF
    clean = content
    for markup in ["[bold]", "[/bold]", "[dim]", "[/dim]", "[red]", "[/red]",
                   "[green]", "[/green]", "[yellow]", "[/yellow]", "[cyan]", "[/cyan]",
                   "[dim yellow]", "[/dim yellow]", "[bold cyan]", "[/bold cyan]"]:
        clean = clean.replace(markup, "")

    # Zeile fuer Zeile ausgeben (multi_cell fuer Umbruch)
    for line in clean.split("\n"):
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue
        # Emojis als Text beibehalten (fpdf2 unterstuetzt Unicode)
        pdf.multi_cell(0, 5, stripped)
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
            return f"✓ PDF-Report gespeichert: {path}"
        except Exception as e:
            return f"❌ PDF-Fehler: {e}"
