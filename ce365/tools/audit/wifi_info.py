"""
CE365 Agent - WiFi Info Tool

SSID, Signalstaerke, Band, Kanal, Sicherheitstyp
macOS: airport utility, networksetup
Windows: netsh wlan show interfaces
"""

import platform
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 10) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.stdout if result.success else ""


class WiFiInfoTool(AuditTool):
    """WiFi-Status und Verbindungsdetails anzeigen"""

    @property
    def name(self) -> str:
        return "check_wifi_info"

    @property
    def description(self) -> str:
        return (
            "Zeigt WiFi-Verbindungsdetails: SSID, Signalstaerke, Band (2.4/5 GHz), "
            "Kanal, Sicherheitstyp, Uebertragungsrate. "
            "Nutze dies bei: 1) WLAN-Probleme, 2) Langsames Internet, "
            "3) Verbindungsabbrueche, 4) WiFi-Audit, "
            "5) Signalstaerke pruefen."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scan_networks": {
                    "type": "boolean",
                    "description": "Auch verfuegbare Netzwerke in der Umgebung scannen",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        scan_networks = kwargs.get("scan_networks", False)
        os_type = platform.system()
        lines = ["📶 WLAN-INFORMATIONEN", "=" * 50, ""]

        if os_type == "Darwin":
            lines.extend(self._macos_wifi_info())
            if scan_networks:
                lines.append("")
                lines.extend(self._macos_scan_networks())
        elif os_type == "Windows":
            lines.extend(self._windows_wifi_info())
            if scan_networks:
                lines.append("")
                lines.extend(self._windows_scan_networks())
        else:
            lines.append("❌ Nicht unterstuetztes Betriebssystem")

        return "\n".join(lines)

    def _macos_wifi_info(self) -> list:
        lines = []

        # airport Utility (seit macOS Sequoia verschoben)
        airport_paths = [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "/System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport",
        ]

        airport_output = ""
        for path in airport_paths:
            airport_output = _run_cmd([path, "-I"], timeout=5)
            if airport_output:
                break

        if not airport_output:
            # Fallback: networksetup
            lines.extend(self._macos_networksetup_fallback())
            return lines

        # airport -I Output parsen
        info = {}
        for line in airport_output.splitlines():
            stripped = line.strip()
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                info[key.strip().lower()] = value.strip()

        ssid = info.get("ssid", "Nicht verbunden")
        bssid = info.get("bssid", "")
        rssi = info.get("agrctlrssi", "")
        noise = info.get("agrctlnoise", "")
        channel = info.get("channel", "")
        tx_rate = info.get("lastTxRate", info.get("lasttxrate", ""))
        security = info.get("link auth", info.get("auth", ""))

        if ssid == "Nicht verbunden" or not ssid:
            lines.append("❌ Nicht mit WLAN verbunden")
            return lines

        lines.append(f"Netzwerk: {ssid}")
        if bssid:
            lines.append(f"BSSID: {bssid}")

        # Signalstaerke bewerten
        if rssi:
            try:
                rssi_val = int(rssi)
                if rssi_val >= -50:
                    signal = "Ausgezeichnet"
                    icon = "🟢"
                elif rssi_val >= -60:
                    signal = "Gut"
                    icon = "🟢"
                elif rssi_val >= -70:
                    signal = "Mittel"
                    icon = "🟡"
                elif rssi_val >= -80:
                    signal = "Schwach"
                    icon = "🟠"
                else:
                    signal = "Sehr schwach"
                    icon = "🔴"
                lines.append(f"Signal: {icon} {rssi} dBm ({signal})")
            except ValueError:
                lines.append(f"Signal: {rssi} dBm")

        if noise:
            lines.append(f"Rauschen: {noise} dBm")

        # Band aus Kanal ableiten
        if channel:
            try:
                ch_num = int(channel.split(",")[0])
                band = "5 GHz" if ch_num > 14 else "2.4 GHz"
                lines.append(f"Kanal: {channel} ({band})")
            except ValueError:
                lines.append(f"Kanal: {channel}")

        if tx_rate:
            lines.append(f"TX-Rate: {tx_rate} Mbps")
        if security:
            lines.append(f"Sicherheit: {security}")

        return lines

    def _macos_networksetup_fallback(self) -> list:
        """Fallback wenn airport nicht verfuegbar"""
        lines = []

        # Aktives WiFi-Interface finden
        output = _run_cmd(["networksetup", "-listallhardwareports"], timeout=5)
        wifi_device = ""
        for i, line in enumerate(output.splitlines()):
            if "Wi-Fi" in line or "AirPort" in line:
                next_lines = output.splitlines()[i + 1 : i + 3]
                for nl in next_lines:
                    if "Device:" in nl:
                        wifi_device = nl.split(":")[1].strip()
                        break

        if wifi_device:
            info = _run_cmd(["networksetup", "-getairportnetwork", wifi_device], timeout=5)
            if info and "Current Wi-Fi Network" in info:
                ssid = info.split(":", 1)[1].strip()
                lines.append(f"Netzwerk: {ssid}")
            else:
                lines.append("❌ Nicht mit WLAN verbunden")
        else:
            lines.append("❌ Kein WLAN-Adapter gefunden")

        return lines

    def _macos_scan_networks(self) -> list:
        lines = ["📡 Verfuegbare Netzwerke:"]

        airport_paths = [
            "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
            "/System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport",
        ]

        scan_output = ""
        for path in airport_paths:
            scan_output = _run_cmd([path, "-s"], timeout=15)
            if scan_output:
                break

        if scan_output:
            for line in scan_output.splitlines()[:15]:
                lines.append(f"   {line.strip()}")
        else:
            lines.append("   ⚠️  Netzwerk-Scan nicht verfuegbar")

        return lines

    def _windows_wifi_info(self) -> list:
        lines = []

        output = _run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=10)
        if not output:
            lines.append("❌ WLAN-Informationen nicht verfuegbar")
            return lines

        info = {}
        for line in output.splitlines():
            if ":" in line:
                key, _, value = line.strip().partition(":")
                info[key.strip().lower()] = value.strip()

        # Deutsche + Englische Keys unterstuetzen
        ssid = info.get("ssid", info.get("ssid", ""))
        state = info.get("state", info.get("status", info.get("zustand", "")))
        signal = info.get("signal", info.get("signal", ""))
        channel = info.get("channel", info.get("kanal", ""))
        radio_type = info.get("radio type", info.get("funktyp", ""))
        auth = info.get("authentication", info.get("authentifizierung", ""))
        rx_rate = info.get("receive rate (mbps)", info.get("empfangsrate (mbit/s)", ""))
        tx_rate = info.get("transmit rate (mbps)", info.get("uebertragungsrate (mbit/s)", ""))
        bssid = info.get("bssid", "")

        if not ssid or "disconnected" in state.lower() or "getrennt" in state.lower():
            lines.append("❌ Nicht mit WLAN verbunden")
            return lines

        lines.append(f"Netzwerk: {ssid}")
        if bssid:
            lines.append(f"BSSID: {bssid}")

        # Signal bewerten
        if signal:
            try:
                sig_val = int(signal.rstrip("%"))
                if sig_val >= 80:
                    icon = "🟢"
                    quality = "Ausgezeichnet"
                elif sig_val >= 60:
                    icon = "🟢"
                    quality = "Gut"
                elif sig_val >= 40:
                    icon = "🟡"
                    quality = "Mittel"
                elif sig_val >= 20:
                    icon = "🟠"
                    quality = "Schwach"
                else:
                    icon = "🔴"
                    quality = "Sehr schwach"
                lines.append(f"Signal: {icon} {signal} ({quality})")
            except ValueError:
                lines.append(f"Signal: {signal}")

        if channel:
            try:
                ch_num = int(channel)
                band = "5 GHz" if ch_num > 14 else "2.4 GHz"
                lines.append(f"Kanal: {channel} ({band})")
            except ValueError:
                lines.append(f"Kanal: {channel}")

        if radio_type:
            lines.append(f"Standard: {radio_type}")
        if auth:
            lines.append(f"Sicherheit: {auth}")
        if rx_rate:
            lines.append(f"Empfangsrate: {rx_rate} Mbps")
        if tx_rate:
            lines.append(f"Senderate: {tx_rate} Mbps")

        return lines

    def _windows_scan_networks(self) -> list:
        lines = ["📡 Verfuegbare Netzwerke:"]

        output = _run_cmd(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=15)
        if output:
            for line in output.splitlines()[:30]:
                stripped = line.strip()
                if stripped:
                    lines.append(f"   {stripped}")
        else:
            lines.append("   ⚠️  Netzwerk-Scan nicht verfuegbar")

        return lines
