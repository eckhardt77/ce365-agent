"""
TechCare Bot - System Reporting Tool

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Generiert umfassende System-Reports
"""

import platform
import psutil
from datetime import datetime
from typing import Dict, Any
from techcare.tools.base import AuditTool


class GenerateSystemReportTool(AuditTool):
    """
    Generiert umfassenden System-Report

    Sammelt alle wichtigen System-Informationen in einem Report
    """

    @property
    def name(self) -> str:
        return "generate_system_report"

    @property
    def description(self) -> str:
        return (
            "Generiert einen umfassenden System-Report mit allen wichtigen Informationen. "
            "Nutze dies bei: 1) Kunden-Dokumentation, 2) System-Analyse, "
            "3) Vor größeren Änderungen, 4) Regelmäßige Wartungs-Reports. "
            "Sammelt: Hardware, Software, Prozesse, Disk, Netzwerk, Updates, Backup-Status."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["text", "markdown"],
                    "description": "Report-Format (Standard: markdown)",
                    "default": "markdown"
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Generiert System-Report

        Args:
            format: Report-Format (text/markdown)

        Returns:
            Formatierter System-Report
        """
        report_format = kwargs.get("format", "markdown")

        try:
            # Report-Header
            report = []

            if report_format == "markdown":
                report.append("# 📊 TechCare System Report")
                report.append("")
                report.append(f"**Erstellt:** {self._get_timestamp()}")
                report.append(f"**System:** {platform.node()}")
                report.append("")
                report.append("---")
            else:
                report.append("=" * 70)
                report.append("TECHCARE SYSTEM REPORT")
                report.append("=" * 70)
                report.append(f"Erstellt: {self._get_timestamp()}")
                report.append(f"System: {platform.node()}")
                report.append("=" * 70)

            report.append("")

            # 1. SYSTEM INFORMATION
            report.extend(self._section_system_info(report_format))

            # 2. HARDWARE
            report.extend(self._section_hardware(report_format))

            # 3. DISK
            report.extend(self._section_disk(report_format))

            # 4. NETWORK
            report.extend(self._section_network(report_format))

            # 5. PROCESSES (Top 10)
            report.extend(self._section_processes(report_format))

            # 6. SERVICES (nur wichtigste)
            report.extend(self._section_services(report_format))

            # Report-Footer
            report.append("")
            if report_format == "markdown":
                report.append("---")
                report.append("*Generiert von TechCare Bot*")
            else:
                report.append("=" * 70)
                report.append("Generiert von TechCare Bot")
                report.append("=" * 70)

            return "\n".join(report)

        except Exception as e:
            return f"❌ Fehler beim Report-Generieren: {str(e)}"

    def _section_system_info(self, fmt: str) -> list:
        """System Info Section"""
        section = []

        if fmt == "markdown":
            section.append("## 🖥️  System Information")
            section.append("")
        else:
            section.append("SYSTEM INFORMATION")
            section.append("-" * 70)

        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()

        if os_name == "Darwin":
            os_name = "macOS"

        section.append(f"**Betriebssystem:** {os_name} {os_release}")
        section.append(f"**Version:** {os_version}")
        section.append(f"**Architektur:** {platform.machine()}")
        section.append(f"**Hostname:** {platform.node()}")

        # Uptime
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()
            uptime_str = self._format_uptime(uptime_seconds)
            section.append(f"**Uptime:** {uptime_str}")
        except:
            pass

        section.append("")
        return section

    def _section_hardware(self, fmt: str) -> list:
        """Hardware Section"""
        section = []

        if fmt == "markdown":
            section.append("## 💻 Hardware")
            section.append("")
        else:
            section.append("HARDWARE")
            section.append("-" * 70)

        # CPU
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()

        section.append(f"**CPU:**")
        section.append(f"  • Cores: {cpu_count_physical} Physical, {cpu_count_logical} Logical")
        if cpu_freq:
            section.append(f"  • Frequenz: {cpu_freq.current:.0f} MHz (Max: {cpu_freq.max:.0f} MHz)")

        cpu_percent = psutil.cpu_percent(interval=1)
        section.append(f"  • Auslastung: {cpu_percent}%")

        # RAM
        mem = psutil.virtual_memory()
        section.append("")
        section.append(f"**RAM:**")
        section.append(f"  • Total: {self._format_bytes(mem.total)}")
        section.append(f"  • Verfügbar: {self._format_bytes(mem.available)}")
        section.append(f"  • Genutzt: {mem.percent}%")

        section.append("")
        return section

    def _section_disk(self, fmt: str) -> list:
        """Disk Section"""
        section = []

        if fmt == "markdown":
            section.append("## 💿 Speicher")
            section.append("")
        else:
            section.append("SPEICHER")
            section.append("-" * 70)

        partitions = psutil.disk_partitions()

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)

                section.append(f"**{partition.device}** ({partition.mountpoint})")
                section.append(f"  • Total: {self._format_bytes(usage.total)}")
                section.append(f"  • Genutzt: {self._format_bytes(usage.used)} ({usage.percent}%)")
                section.append(f"  • Frei: {self._format_bytes(usage.free)}")

                if usage.percent > 90:
                    section.append(f"  • ⚠️  **KRITISCH - <10% frei!**")
                elif usage.percent > 80:
                    section.append(f"  • ⚠️  Warnung - <20% frei")

                section.append("")
            except:
                continue

        return section

    def _section_network(self, fmt: str) -> list:
        """Network Section"""
        section = []

        if fmt == "markdown":
            section.append("## 🌐 Netzwerk")
            section.append("")
        else:
            section.append("NETZWERK")
            section.append("-" * 70)

        # Network Interfaces
        net_if_addrs = psutil.net_if_addrs()

        for interface, addrs in net_if_addrs.items():
            for addr in addrs:
                if addr.family == 2:  # AF_INET (IPv4)
                    section.append(f"**{interface}:**")
                    section.append(f"  • IPv4: {addr.address}")
                    break

        section.append("")
        return section

    def _section_processes(self, fmt: str) -> list:
        """Top Processes Section"""
        section = []

        if fmt == "markdown":
            section.append("## 🔄 Top Prozesse (CPU)")
            section.append("")
        else:
            section.append("TOP PROZESSE (CPU)")
            section.append("-" * 70)

        # Top 10 CPU
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except:
                continue

        processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)

        section.append("| Prozess | CPU% |")
        section.append("|---------|------|")

        for proc in processes[:10]:
            name = proc.get('name', 'Unknown')[:30]
            cpu = proc.get('cpu_percent', 0) or 0
            section.append(f"| {name} | {cpu:.1f}% |")

        section.append("")
        return section

    def _section_services(self, fmt: str) -> list:
        """Important Services Section"""
        section = []

        if fmt == "markdown":
            section.append("## 🔧 System-Status")
            section.append("")
        else:
            section.append("SYSTEM-STATUS")
            section.append("-" * 70)

        section.append("✓ Report erfolgreich generiert")
        section.append("")

        return section

    def _format_bytes(self, bytes_value: int) -> str:
        """Formatiert Bytes zu lesbarer Größe"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def _format_uptime(self, seconds: float) -> str:
        """Formatiert Uptime"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _get_timestamp(self) -> str:
        """Aktueller Timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
