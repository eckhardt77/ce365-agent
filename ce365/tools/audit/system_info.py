import platform
import subprocess
import psutil
from datetime import datetime, timedelta
from ce365.tools.base import AuditTool


# ============================================================
# macOS Codename-Mapping
# ============================================================
_MACOS_CODENAMES = {
    "15": "Sequoia",
    "14": "Sonoma",
    "13": "Ventura",
    "12": "Monterey",
    "11": "Big Sur",
    "10.15": "Catalina",
    "10.14": "Mojave",
}


def _run_cmd(cmd: list, timeout: int = 3) -> str:
    """Subprocess ausfuehren, Ergebnis als String oder leer bei Fehler"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def _parse_wmic_value(output: str) -> str:
    """Parst 'Key=Value' Output von wmic /value"""
    for line in output.splitlines():
        if "=" in line:
            return line.split("=", 1)[1].strip()
    return ""


# ============================================================
# Plattform-spezifische Befueller
# ============================================================

def _fill_macos_info(info: dict):
    """macOS-spezifische Hardware-Daten fuellen"""
    # OS Name mit Codename
    mac_ver = platform.mac_ver()[0]
    if mac_ver:
        major = mac_ver.split(".")[0]
        codename = _MACOS_CODENAMES.get(major, "")
        if codename:
            info["os_name"] = f"macOS {mac_ver} {codename}"
        else:
            info["os_name"] = f"macOS {mac_ver}"
    else:
        info["os_name"] = "macOS"

    # CPU Name
    cpu = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
    if cpu:
        info["cpu_name"] = cpu

    # Hersteller
    info["manufacturer"] = "Apple Inc."

    # Modell + Serial via system_profiler SPHardwareDataType
    hw_output = _run_cmd(["system_profiler", "SPHardwareDataType", "-detailLevel", "mini"])
    if hw_output:
        for line in hw_output.splitlines():
            stripped = line.strip()
            if stripped.startswith("Model Name:"):
                info["model"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("Serial Number"):
                info["serial"] = stripped.split(":", 1)[1].strip()

    # GPU via system_profiler SPDisplaysDataType
    gpu_output = _run_cmd(["system_profiler", "SPDisplaysDataType", "-detailLevel", "mini"])
    if gpu_output:
        for line in gpu_output.splitlines():
            stripped = line.strip()
            if stripped.startswith("Chipset Model:"):
                info["gpu"] = stripped.split(":", 1)[1].strip()
                break

    # Disk-Typ via system_profiler SPStorageDataType
    storage_output = _run_cmd(["system_profiler", "SPStorageDataType", "-detailLevel", "mini"])
    if storage_output:
        for line in storage_output.splitlines():
            stripped = line.strip()
            if stripped.startswith("Medium Type:") or stripped.startswith("Type:"):
                medium = stripped.split(":", 1)[1].strip()
                if "SSD" in medium.upper() or "SOLID" in medium.upper():
                    info["disk_type"] = "SSD"
                elif "HDD" in medium.upper() or "ROTATIONAL" in medium.upper():
                    info["disk_type"] = "HDD"
                else:
                    info["disk_type"] = medium
                break
        # NVMe-Erkennung aus Protocol-Zeile
        if not info["disk_type"]:
            for line in storage_output.splitlines():
                stripped = line.strip()
                if "NVMe" in stripped:
                    info["disk_type"] = "NVMe SSD"
                    break


def _fill_windows_info(info: dict):
    """Windows-spezifische Hardware-Daten fuellen"""
    # OS Name
    os_caption = _parse_wmic_value(_run_cmd(["wmic", "os", "get", "caption", "/value"]))
    if os_caption:
        # "Microsoft Windows 11 Pro" -> "Windows 11 Pro"
        info["os_name"] = os_caption.replace("Microsoft ", "")
    else:
        info["os_name"] = f"Windows {platform.release()}"

    # CPU Name
    cpu = _parse_wmic_value(_run_cmd(["wmic", "cpu", "get", "name", "/value"]))
    if cpu:
        info["cpu_name"] = cpu

    # GPU
    gpu = _parse_wmic_value(_run_cmd(["wmic", "path", "win32_VideoController", "get", "name", "/value"]))
    if gpu:
        info["gpu"] = gpu

    # Hersteller
    vendor = _parse_wmic_value(_run_cmd(["wmic", "csproduct", "get", "vendor", "/value"]))
    if vendor:
        info["manufacturer"] = vendor

    # Modell
    model = _parse_wmic_value(_run_cmd(["wmic", "csproduct", "get", "name", "/value"]))
    if model:
        info["model"] = model

    # Seriennummer
    serial = _parse_wmic_value(_run_cmd(["wmic", "bios", "get", "serialnumber", "/value"]))
    if serial:
        info["serial"] = serial

    # Disk-Typ
    disk_output = _run_cmd(["wmic", "diskdrive", "get", "model,mediatype", "/value"])
    if disk_output:
        media = _parse_wmic_value(disk_output)
        if media:
            if "SSD" in media.upper() or "SOLID" in media.upper() or "NVME" in media.upper():
                info["disk_type"] = "NVMe SSD" if "NVME" in media.upper() else "SSD"
            elif "HDD" in media.upper() or "FIXED" in media.upper():
                info["disk_type"] = "HDD"
            else:
                info["disk_type"] = media


def _fill_battery_info(info: dict):
    """Battery-Info plattformuebergreifend via psutil"""
    try:
        battery = psutil.sensors_battery()
        if battery is not None:
            info["battery"] = {
                "percent": round(battery.percent),
                "plugged_in": battery.power_plugged,
            }
    except Exception:
        pass


# ============================================================
# Hauptfunktion
# ============================================================

def get_hardware_info() -> dict:
    """
    Plattformuebergreifende Hardware-Erkennung.

    Returns:
        Dict mit allen Hardware-Informationen.
        Fehlende Daten = leerer String / None.
    """
    info = {
        "os_name": "",
        "cpu_name": "",
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "gpu": "",
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "manufacturer": "",
        "model": "",
        "serial": "",
        "disk_type": "",
        "battery": None,
    }

    if platform.system() == "Darwin":
        _fill_macos_info(info)
    elif platform.system() == "Windows":
        _fill_windows_info(info)
    else:
        # Linux Fallback
        info["os_name"] = f"{platform.system()} {platform.release()}"

    _fill_battery_info(info)
    return info


def get_mac_hardware() -> dict:
    """Legacy-Wrapper — nutzt get_hardware_info() intern"""
    hw = get_hardware_info()
    result = {}
    if hw["cpu_name"]:
        result["chip"] = hw["cpu_name"]
    if hw["model"]:
        result["model_id"] = hw["model"]
    return result


def _get_primary_disk_path() -> str:
    """Primaeres Laufwerk plattformuebergreifend"""
    if platform.system() == "Windows":
        return "C:\\"
    return "/"


class SystemInfoTool(AuditTool):
    """
    System-Informationen sammeln (Read-Only)

    Informationen:
    - OS (Windows/macOS/Linux)
    - CPU (Name, Kerne, Auslastung)
    - GPU
    - RAM (Total, Used, Free)
    - Disk (Total, Used, Free)
    - Hersteller / Modell
    - Uptime
    - Battery (wenn Laptop)
    """

    @property
    def name(self) -> str:
        return "get_system_info"

    @property
    def description(self) -> str:
        return (
            "Sammelt System-Informationen (OS, CPU, GPU, RAM, Disk, Hersteller, Modell, Uptime). "
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
        hw = get_hardware_info()
        lines = []

        # OS Info
        lines.append("🖥️  SYSTEM-INFORMATIONEN")
        lines.append("=" * 50)
        lines.append(f"Betriebssystem: {hw['os_name']}")
        lines.append(f"Version: {platform.version()}")

        # Architektur mit CPU-Name
        arch = platform.machine()
        if hw["cpu_name"]:
            lines.append(f"Architektur: {arch} ({hw['cpu_name']})")
        else:
            lines.append(f"Architektur: {arch}")

        # Hersteller / Modell
        if hw["manufacturer"] or hw["model"]:
            hw_line = ""
            if hw["manufacturer"]:
                hw_line += hw["manufacturer"]
            if hw["model"]:
                if hw_line:
                    hw_line += " "
                hw_line += hw["model"]
            lines.append(f"Geraet: {hw_line}")

        if hw["serial"]:
            lines.append(f"Seriennummer: {hw['serial']}")

        lines.append(f"Hostname: {platform.node()}")
        lines.append("")

        # CPU
        cpu_count = hw["cpu_cores_logical"]
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_label = hw["cpu_name"] if hw["cpu_name"] else f"{cpu_count} Kerne"
        lines.append(f"💻 CPU: {cpu_label}")
        lines.append(f"   Kerne: {hw['cpu_cores_physical']} Physical, {cpu_count} Logical")
        lines.append(f"   Auslastung: {cpu_percent}%")
        lines.append("")

        # GPU
        if hw["gpu"]:
            lines.append(f"🎮 GPU: {hw['gpu']}")
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

        # Disk (plattformuebergreifend)
        disk_path = _get_primary_disk_path()
        try:
            disk = psutil.disk_usage(disk_path)
            disk_total_gb = disk.total / (1024**3)
            disk_used_gb = disk.used / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            disk_label = f"💾 Disk ({disk_path})"
            if hw["disk_type"]:
                disk_label += f" [{hw['disk_type']}]"
            lines.append(f"{disk_label}:")
            lines.append(f"   Total: {disk_total_gb:.2f} GB")
            lines.append(f"   Belegt: {disk_used_gb:.2f} GB ({disk.percent}%)")
            lines.append(f"   Frei: {disk_free_gb:.2f} GB")
            lines.append("")
        except Exception:
            lines.append(f"💾 Disk: Nicht verfuegbar")
            lines.append("")

        # Battery
        if hw["battery"]:
            bat = hw["battery"]
            plug = "⚡ Netzbetrieb" if bat["plugged_in"] else "🔋 Akku"
            lines.append(f"🔋 Akku: {bat['percent']}% ({plug})")
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

            # Alle Partitionen
            lines.append("")
            lines.append("Alle Partitionen:")
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total_gb = usage.total / (1024**3)
                    lines.append(f"   {part.device} ({part.mountpoint}): {total_gb:.1f} GB, {usage.percent}% belegt")
                except Exception:
                    lines.append(f"   {part.device} ({part.mountpoint}): nicht zugreifbar")

        return "\n".join(lines)
