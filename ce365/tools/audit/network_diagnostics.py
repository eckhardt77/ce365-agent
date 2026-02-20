"""
CE365 Agent - Network Diagnostics Tools

Ping, Traceroute, DNS-Lookup, Port-Check
Plattformuebergreifend: macOS + Windows
"""

import platform
import socket
from typing import Dict, Any
from ce365.tools.base import AuditTool
from ce365.core.command_runner import get_command_runner


def _run_cmd(cmd: list, timeout: int = 15) -> str:
    result = get_command_runner().run_sync(cmd, timeout=timeout)
    return result.output


class NetworkDiagnosticsTool(AuditTool):
    """Netzwerk-Diagnose: Ping, Traceroute, DNS-Lookup, Port-Check"""

    @property
    def name(self) -> str:
        return "network_diagnostics"

    @property
    def description(self) -> str:
        return (
            "Fuehrt Netzwerk-Diagnosen durch: Ping, Traceroute, DNS-Lookup, Port-Check. "
            "Nutze dies bei: 1) Keine Internet-Verbindung, 2) Langsames Netzwerk, "
            "3) Website nicht erreichbar, 4) DNS-Probleme, 5) Port-Blockierung. "
            "Waehle die gewuenschte Aktion ueber den 'action' Parameter."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["ping", "traceroute", "dns_lookup", "port_check", "full_check"],
                    "description": "Diagnose-Aktion: ping, traceroute, dns_lookup, port_check, full_check (alle)",
                },
                "host": {
                    "type": "string",
                    "description": "Ziel-Host/IP (z.B. google.com, 8.8.8.8). Standard: google.com",
                    "default": "google.com",
                },
                "port": {
                    "type": "integer",
                    "description": "Port fuer port_check (Standard: 443)",
                    "default": 443,
                },
            },
            "required": ["action"],
        }

    async def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "full_check")
        host = kwargs.get("host", "google.com")
        port = kwargs.get("port", 443)

        # Host validieren — keine Shell-Injection
        host = host.strip().replace(";", "").replace("&", "").replace("|", "")
        if not host:
            return "❌ Kein Host angegeben"

        lines = []

        if action == "ping":
            lines.extend(self._ping(host))
        elif action == "traceroute":
            lines.extend(self._traceroute(host))
        elif action == "dns_lookup":
            lines.extend(self._dns_lookup(host))
        elif action == "port_check":
            lines.extend(self._port_check(host, port))
        elif action == "full_check":
            lines.append("🌐 NETZWERK-DIAGNOSE (Vollstaendig)")
            lines.append("=" * 50)
            lines.append("")
            lines.extend(self._ping(host))
            lines.append("")
            lines.extend(self._dns_lookup(host))
            lines.append("")
            lines.extend(self._port_check(host, 80))
            lines.extend(self._port_check(host, 443))
            lines.append("")
            # Auch Default-Gateway + oeffentliche IP
            lines.extend(self._gateway_check())
            lines.append("")
            lines.extend(self._public_ip())

        return "\n".join(lines)

    def _ping(self, host: str) -> list:
        lines = [f"📡 Ping → {host}"]
        os_type = platform.system()

        if os_type == "Windows":
            cmd = ["ping", "-n", "4", host]
        else:
            cmd = ["ping", "-c", "4", "-W", "3", host]

        output = _run_cmd(cmd, timeout=20)

        if "Timeout" in output or "100% packet loss" in output or "100% Paketverlust" in output:
            lines.append(f"   ❌ Host {host} nicht erreichbar")
        elif "0% packet loss" in output or "0% Paketverlust" in output:
            lines.append(f"   ✅ Host erreichbar (0% Paketverlust)")
            # Latenz extrahieren
            for line in output.splitlines():
                if "avg" in line.lower() or "mittel" in line.lower() or "average" in line.lower():
                    lines.append(f"   ⏱️  {line.strip()}")
                    break
        else:
            lines.append(f"   ⚠️  Teilweise erreichbar")

        # Letzte Zeilen mit Statistik
        result_lines = output.splitlines()
        for rl in result_lines[-3:]:
            stripped = rl.strip()
            if stripped and ("ms" in stripped or "Pakete" in stripped or "packets" in stripped.lower()):
                lines.append(f"   {stripped}")

        return lines

    def _traceroute(self, host: str) -> list:
        lines = [f"🗺️  Traceroute → {host}"]
        os_type = platform.system()

        if os_type == "Windows":
            cmd = ["tracert", "-d", "-w", "2000", "-h", "15", host]
        else:
            cmd = ["traceroute", "-n", "-m", "15", "-w", "2", host]

        output = _run_cmd(cmd, timeout=60)

        if output:
            for line in output.splitlines()[:20]:
                stripped = line.strip()
                if stripped:
                    lines.append(f"   {stripped}")
        else:
            lines.append("   ❌ Traceroute fehlgeschlagen")

        return lines

    def _dns_lookup(self, host: str) -> list:
        lines = [f"🔍 DNS-Lookup → {host}"]

        try:
            # Python-native DNS-Aufloesung
            results = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            seen = set()
            for family, _, _, _, sockaddr in results:
                ip = sockaddr[0]
                if ip not in seen:
                    seen.add(ip)
                    ip_type = "IPv6" if family == socket.AF_INET6 else "IPv4"
                    lines.append(f"   ✅ {ip_type}: {ip}")

            if not seen:
                lines.append(f"   ❌ Keine DNS-Aufloesung moeglich")
        except socket.gaierror:
            lines.append(f"   ❌ DNS-Aufloesung fehlgeschlagen fuer '{host}'")
            lines.append(f"   → DNS-Server pruefen oder Host-Name korrigieren")
        except Exception as e:
            lines.append(f"   ❌ Fehler: {e}")

        # Konfigurierte DNS-Server anzeigen
        os_type = platform.system()
        if os_type == "Darwin":
            dns_out = _run_cmd(["scutil", "--dns"], timeout=5)
            if dns_out:
                for line in dns_out.splitlines():
                    if "nameserver" in line.lower():
                        lines.append(f"   DNS-Server: {line.strip()}")
                        break
        elif os_type == "Windows":
            dns_out = _run_cmd(["nslookup", host], timeout=10)
            if dns_out:
                for line in dns_out.splitlines()[:3]:
                    stripped = line.strip()
                    if stripped and ("Server" in stripped or "Address" in stripped):
                        lines.append(f"   {stripped}")

        return lines

    def _port_check(self, host: str, port: int) -> list:
        lines = [f"🔌 Port-Check → {host}:{port}"]

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                # Bekannte Dienste
                services = {
                    22: "SSH", 25: "SMTP", 53: "DNS", 80: "HTTP", 443: "HTTPS",
                    445: "SMB", 993: "IMAPS", 3306: "MySQL", 3389: "RDP",
                    5432: "PostgreSQL", 8080: "HTTP-Alt",
                }
                service = services.get(port, "")
                suffix = f" ({service})" if service else ""
                lines.append(f"   ✅ Port {port}{suffix} ist offen")
            else:
                lines.append(f"   ❌ Port {port} ist geschlossen/blockiert")
        except socket.timeout:
            lines.append(f"   ❌ Port {port} — Timeout (Firewall blockiert?)")
        except Exception as e:
            lines.append(f"   ❌ Fehler: {e}")

        return lines

    def _gateway_check(self) -> list:
        lines = ["🚪 Default Gateway"]
        os_type = platform.system()

        if os_type == "Darwin":
            output = _run_cmd(["route", "-n", "get", "default"], timeout=5)
            for line in output.splitlines():
                if "gateway" in line.lower():
                    gw = line.split(":")[-1].strip()
                    lines.append(f"   Gateway: {gw}")
                    # Gateway anpingen
                    ping_result = _run_cmd(["ping", "-c", "1", "-W", "2", gw], timeout=5)
                    if "1 packets received" in ping_result or "0% packet loss" in ping_result:
                        lines.append(f"   ✅ Gateway erreichbar")
                    else:
                        lines.append(f"   ❌ Gateway nicht erreichbar!")
                    break
        elif os_type == "Windows":
            output = _run_cmd(["ipconfig"], timeout=5)
            for line in output.splitlines():
                if "gateway" in line.lower() or "Standardgateway" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        gw = parts[-1].strip()
                        if gw:
                            lines.append(f"   Gateway: {gw}")
                            break

        if len(lines) == 1:
            lines.append("   ⚠️  Kein Default Gateway gefunden")

        return lines

    def _public_ip(self) -> list:
        lines = ["🌍 Oeffentliche IP"]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            lines.append(f"   Lokale IP: {local_ip}")
        except Exception:
            lines.append("   ❌ Keine Netzwerkverbindung")

        return lines
