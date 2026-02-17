import platform
import psutil
from datetime import datetime, timedelta
from ce365.tools.base import AuditTool


class SystemInfoTool(AuditTool):
    """
    System-Informationen sammeln (Read-Only)

    Informationen:
    - OS (Windows/macOS/Linux)
    - CPU (Kerne, Auslastung)
    - RAM (Total, Used, Free)
    - Disk (Total, Used, Free)
    - Uptime
    """

    @property
    def name(self) -> str:
        return "get_system_info"

    @property
    def description(self) -> str:
        return (
            "Sammelt System-Informationen (OS, CPU, RAM, Disk, Uptime). "
            "Read-Only Tool für initiale Diagnose."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Detaillierte Informationen anzeigen (optional)",
                    "default": False,
                }
            },
            "required": [],
        }

    async def execute(self, detailed: bool = False) -> str:
        """System-Info sammeln"""
        lines = []

        # OS Info
        lines.append("🖥️  SYSTEM-INFORMATIONEN")
        lines.append("=" * 50)
        lines.append(f"Betriebssystem: {platform.system()} {platform.release()}")
        lines.append(f"Version: {platform.version()}")
        lines.append(f"Architektur: {platform.machine()}")
        lines.append(f"Hostname: {platform.node()}")
        lines.append("")

        # CPU
        cpu_count = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent(interval=1)
        lines.append(f"💻 CPU: {cpu_count} Kerne")
        lines.append(f"   Auslastung: {cpu_percent}%")
        lines.append("")

        # RAM
        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024**3)
        ram_used_gb = ram.used / (1024**3)
        ram_free_gb = ram.available / (1024**3)
        lines.append(f"🧠 RAM:")
        lines.append(f"   Total: {ram_total_gb:.2f} GB")
        lines.append(f"   Belegt: {ram_used_gb:.2f} GB ({ram.percent}%)")
        lines.append(f"   Frei: {ram_free_gb:.2f} GB")
        lines.append("")

        # Disk
        disk = psutil.disk_usage("/")
        disk_total_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        disk_free_gb = disk.free / (1024**3)
        lines.append(f"💾 Disk (/):")
        lines.append(f"   Total: {disk_total_gb:.2f} GB")
        lines.append(f"   Belegt: {disk_used_gb:.2f} GB ({disk.percent}%)")
        lines.append(f"   Frei: {disk_free_gb:.2f} GB")
        lines.append("")

        # Uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        lines.append(f"⏱️  Uptime: {days}d {hours}h {minutes}m")
        lines.append(f"   Letzter Boot: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if detailed:
            lines.append("")
            lines.append("=" * 50)
            lines.append("DETAILLIERTE INFORMATIONEN")
            lines.append("=" * 50)

            # CPU Details
            if hasattr(psutil, "cpu_freq"):
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    lines.append(f"CPU Frequenz: {cpu_freq.current:.2f} MHz")

            # Per-Core CPU Usage
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            lines.append(f"CPU per Core: {', '.join(f'{c}%' for c in cpu_per_core)}")

            # Swap Memory
            swap = psutil.swap_memory()
            swap_total_gb = swap.total / (1024**3)
            swap_used_gb = swap.used / (1024**3)
            lines.append("")
            lines.append(f"Swap Memory:")
            lines.append(f"   Total: {swap_total_gb:.2f} GB")
            lines.append(f"   Belegt: {swap_used_gb:.2f} GB ({swap.percent}%)")

        return "\n".join(lines)
