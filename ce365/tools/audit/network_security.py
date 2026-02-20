"""
CE365 Agent - Network Security Audit

Open Ports, lauschende Services, verdaechtige Verbindungen
Plattformuebergreifend via psutil + native Tools
"""

import platform
import subprocess
import psutil
import socket
from typing import Dict, Any
from ce365.tools.base import AuditTool


# Bekannte gutartige Ports
_KNOWN_SAFE_PORTS = {
    22: "SSH", 53: "DNS", 80: "HTTP", 443: "HTTPS",
    123: "NTP", 137: "NetBIOS", 138: "NetBIOS", 139: "NetBIOS",
    445: "SMB", 631: "CUPS/IPP", 993: "IMAPS", 995: "POP3S",
    5353: "mDNS/Bonjour", 5355: "LLMNR",
}

# Verdaechtige Ports (oft von Malware genutzt)
_SUSPICIOUS_PORTS = {
    4444: "Metasploit default", 5555: "Android ADB",
    6666: "IRC Backdoor", 6667: "IRC", 1337: "Backdoor",
    31337: "Back Orifice", 12345: "NetBus", 27374: "SubSeven",
    8888: "Unspecified Service",
}


class NetworkSecurityAuditTool(AuditTool):
    """Open Ports, lauschende Dienste und verdaechtige Verbindungen pruefen"""

    @property
    def name(self) -> str:
        return "check_network_security"

    @property
    def description(self) -> str:
        return (
            "Prueft Netzwerk-Sicherheit: offene Ports, lauschende Dienste, "
            "verdaechtige Verbindungen, unbekannte Listener. "
            "Nutze dies bei: 1) Sicherheits-Audit, 2) Verdacht auf Malware/Backdoor, "
            "3) Unbekannter Netzwerk-Traffic, 4) Port-Konflikte, "
            "5) Firewall-Tuning."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "show_established": {
                    "type": "boolean",
                    "description": "Auch etablierte Verbindungen anzeigen (nicht nur Listener)",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        show_established = kwargs.get("show_established", False)
        lines = ["🔒 NETZWERK-SICHERHEIT", "=" * 50, ""]

        try:
            # 1. Lauschende Ports
            lines.extend(self._check_listening_ports())
            lines.append("")

            # 2. Verdaechtige Verbindungen
            lines.extend(self._check_suspicious_connections())
            lines.append("")

            # 3. Etablierte Verbindungen (optional)
            if show_established:
                lines.extend(self._check_established_connections())
                lines.append("")

            # 4. Zusammenfassung
            lines.extend(self._summary())
        except PermissionError:
            lines.append("⚠️  Fuer vollstaendige Netzwerk-Analyse werden erhoehte Rechte benoetigt.")
            lines.append("   macOS: sudo ausfuehren | Windows: Als Administrator starten")
            lines.append("")
            # Fallback: lsof/netstat statt psutil
            lines.extend(self._fallback_netstat())

        return "\n".join(lines)

    def _check_listening_ports(self) -> list:
        lines = ["📡 Lauschende Ports (LISTEN):"]
        lines.append("")

        try:
            connections = psutil.net_connections(kind="inet")
        except (PermissionError, psutil.AccessDenied):
            raise PermissionError("psutil.net_connections benoetigt Root-Rechte")

        listeners = [c for c in connections if c.status == "LISTEN"]

        # Nach Port sortieren
        listeners.sort(key=lambda c: c.laddr.port)

        suspicious_found = []

        for conn in listeners:
            port = conn.laddr.port
            addr = conn.laddr.ip
            pid = conn.pid

            # Prozess-Name ermitteln
            proc_name = "?"
            if pid:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Klassifizierung
            if port in _SUSPICIOUS_PORTS:
                icon = "🔴"
                note = f"VERDAECHTIG: {_SUSPICIOUS_PORTS[port]}"
                suspicious_found.append((port, proc_name, note))
            elif port in _KNOWN_SAFE_PORTS:
                icon = "🟢"
                note = _KNOWN_SAFE_PORTS[port]
            elif port < 1024:
                icon = "🟡"
                note = "System-Port"
            else:
                icon = "⚪"
                note = ""

            line = f"   {icon} Port {port:>5} ({addr}) — {proc_name}"
            if note:
                line += f" [{note}]"
            if pid:
                line += f" (PID: {pid})"
            lines.append(line)

        if not listeners:
            lines.append("   Keine lauschenden Ports gefunden.")

        if suspicious_found:
            lines.append("")
            lines.append("   ⚠️  VERDAECHTIGE PORTS GEFUNDEN:")
            for port, proc, note in suspicious_found:
                lines.append(f"      🔴 Port {port} — {proc} — {note}")

        return lines

    def _check_suspicious_connections(self) -> list:
        lines = ["🔍 Verdaechtige Verbindungen:"]
        lines.append("")

        connections = psutil.net_connections(kind="inet")
        established = [c for c in connections if c.status == "ESTABLISHED" and c.raddr]

        suspicious = []
        for conn in established:
            remote_ip = conn.raddr.ip
            remote_port = conn.raddr.port
            pid = conn.pid

            proc_name = "?"
            if pid:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                except:
                    pass

            # Verdaechtig wenn:
            is_suspicious = False
            reason = ""

            # 1. Verbindung zu bekannt boesartigen Ports
            if remote_port in _SUSPICIOUS_PORTS:
                is_suspicious = True
                reason = f"Verdaechtiger Remote-Port: {_SUSPICIOUS_PORTS[remote_port]}"

            # 2. Nicht-Standard Ports bei unbekannten Prozessen
            if remote_port not in _KNOWN_SAFE_PORTS and remote_port > 10000:
                if proc_name in ("?", "svchost.exe"):
                    is_suspicious = True
                    reason = f"Unbekannter High-Port ({remote_port}) von {proc_name}"

            if is_suspicious:
                suspicious.append({
                    "remote_ip": remote_ip,
                    "remote_port": remote_port,
                    "process": proc_name,
                    "pid": pid,
                    "reason": reason,
                })

        if suspicious:
            for s in suspicious:
                lines.append(
                    f"   🔴 {s['remote_ip']}:{s['remote_port']} ← {s['process']} "
                    f"(PID: {s['pid']}) — {s['reason']}"
                )
        else:
            lines.append("   ✅ Keine verdaechtigen Verbindungen erkannt")

        return lines

    def _check_established_connections(self) -> list:
        lines = ["🌐 Etablierte Verbindungen:"]
        lines.append("")

        connections = psutil.net_connections(kind="inet")
        established = [c for c in connections if c.status == "ESTABLISHED" and c.raddr]

        # Nach Remote-IP gruppieren
        by_process = {}
        for conn in established:
            pid = conn.pid or 0
            proc_name = "?"
            if pid:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()
                except:
                    pass

            key = proc_name
            if key not in by_process:
                by_process[key] = []
            by_process[key].append(f"{conn.raddr.ip}:{conn.raddr.port}")

        for proc_name, targets in sorted(by_process.items()):
            lines.append(f"   {proc_name} ({len(targets)} Verbindungen):")
            for target in targets[:5]:
                lines.append(f"      → {target}")
            if len(targets) > 5:
                lines.append(f"      ... und {len(targets) - 5} weitere")

        if not by_process:
            lines.append("   Keine etablierten Verbindungen.")

        return lines

    def _summary(self) -> list:
        lines = ["📊 Zusammenfassung:"]

        connections = psutil.net_connections(kind="inet")
        listen_count = sum(1 for c in connections if c.status == "LISTEN")
        established_count = sum(1 for c in connections if c.status == "ESTABLISHED")
        total = len(connections)

        lines.append(f"   Lauschende Ports: {listen_count}")
        lines.append(f"   Etablierte Verbindungen: {established_count}")
        lines.append(f"   Gesamt Sockets: {total}")

        return lines

    def _fallback_netstat(self) -> list:
        """Fallback wenn psutil keine Rechte hat — nutzt netstat/lsof"""
        lines = ["📡 Lauschende Ports (via netstat):"]
        lines.append("")

        os_type = platform.system()
        try:
            if os_type == "Darwin":
                result = subprocess.run(
                    ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                    capture_output=True, text=True, timeout=10,
                )
            else:
                result = subprocess.run(
                    ["netstat", "-an"],
                    capture_output=True, text=True, timeout=10,
                )

            if result.stdout:
                for line in result.stdout.splitlines()[:30]:
                    stripped = line.strip()
                    if stripped and ("LISTEN" in stripped or "ESTABLISHED" in stripped):
                        lines.append(f"   {stripped}")
            else:
                lines.append("   Keine Daten verfuegbar")
        except Exception as e:
            lines.append(f"   Fehler: {e}")

        return lines
