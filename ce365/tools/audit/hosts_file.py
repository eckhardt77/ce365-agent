"""
CE365 Agent - Hosts File Viewer

Zeigt und prueft /etc/hosts (macOS/Linux) bzw. Windows hosts Datei
Erkennt Anomalien und verdaechtige Eintraege
"""

import platform
from pathlib import Path
from typing import Dict, Any
from ce365.tools.base import AuditTool


# Bekannte gutartige Hosts-Eintraege
_SAFE_HOSTS = {
    "localhost", "broadcasthost", "ip6-localhost", "ip6-loopback",
    "ip6-localnet", "ip6-mcastprefix", "ip6-allnodes", "ip6-allrouters",
}

# Verdaechtige Domains (Tracking/Malware Redirect)
_SUSPICIOUS_PATTERNS = [
    "facebook.com", "google.com", "microsoft.com", "apple.com",
    "windows.com", "windowsupdate.com", "update.microsoft.com",
]


class HostsFileViewerTool(AuditTool):
    """Hosts-Datei anzeigen und auf Anomalien pruefen"""

    @property
    def name(self) -> str:
        return "check_hosts_file"

    @property
    def description(self) -> str:
        return (
            "Zeigt die Hosts-Datei und prueft auf Anomalien. "
            "Nutze dies bei: 1) Website-Weiterleitungsprobleme, "
            "2) DNS-Probleme trotz funktionierendem DNS, "
            "3) Verdacht auf Malware-Manipulation, "
            "4) Sicherheits-Audit. "
            "Erkennt verdaechtige Eintraege automatisch."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        os_type = platform.system()
        lines = ["📄 HOSTS-DATEI ANALYSE", "=" * 50, ""]

        if os_type == "Darwin":
            hosts_path = Path("/etc/hosts")
        elif os_type == "Windows":
            system_root = Path("C:/Windows")
            hosts_path = system_root / "System32" / "drivers" / "etc" / "hosts"
        else:
            hosts_path = Path("/etc/hosts")

        lines.append(f"Pfad: {hosts_path}")
        lines.append("")

        if not hosts_path.exists():
            lines.append("❌ Hosts-Datei nicht gefunden!")
            return "\n".join(lines)

        try:
            content = hosts_path.read_text(encoding="utf-8", errors="replace")
        except PermissionError:
            lines.append("❌ Keine Berechtigung zum Lesen der Hosts-Datei")
            return "\n".join(lines)
        except Exception as e:
            lines.append(f"❌ Fehler: {e}")
            return "\n".join(lines)

        # Parsen
        entries = []
        comments = 0
        empty = 0
        suspicious = []

        for line_num, raw_line in enumerate(content.splitlines(), 1):
            stripped = raw_line.strip()

            if not stripped:
                empty += 1
                continue
            if stripped.startswith("#"):
                comments += 1
                continue

            # Aktiver Eintrag
            parts = stripped.split()
            if len(parts) >= 2:
                ip = parts[0]
                hostnames = parts[1:]

                for hostname in hostnames:
                    hostname_lower = hostname.lower()
                    entry = {"ip": ip, "hostname": hostname, "line": line_num}
                    entries.append(entry)

                    # Verdaechtig pruefen
                    if hostname_lower not in _SAFE_HOSTS:
                        # Bekannte Domains auf 127.0.0.1/0.0.0.0 = Blocker (oft OK)
                        is_blocker = ip in ("127.0.0.1", "0.0.0.0", "::1")

                        # Redirect auf andere IP = verdaechtig
                        if not is_blocker and ip not in ("127.0.0.1", "0.0.0.0", "::1", "255.255.255.255"):
                            for pattern in _SUSPICIOUS_PATTERNS:
                                if pattern in hostname_lower:
                                    suspicious.append({
                                        "line": line_num,
                                        "ip": ip,
                                        "hostname": hostname,
                                        "reason": f"Bekannte Domain wird auf {ip} umgeleitet!",
                                    })

                        # Jede nicht-localhost Umleitung ist erwaehnenswert
                        if not is_blocker and ip not in ("127.0.0.1", "0.0.0.0", "::1", "255.255.255.255", "fe80::1%lo0"):
                            suspicious.append({
                                "line": line_num,
                                "ip": ip,
                                "hostname": hostname,
                                "reason": f"Benutzerdefinierte Umleitung auf {ip}",
                            })

        # Ausgabe
        lines.append("📊 Uebersicht:")
        lines.append(f"   Aktive Eintraege: {len(entries)}")
        lines.append(f"   Kommentare: {comments}")
        lines.append(f"   Leerzeilen: {empty}")
        lines.append("")

        # Alle aktiven Eintraege
        if entries:
            lines.append("📝 Aktive Eintraege:")
            for entry in entries:
                hostname = entry["hostname"]
                ip = entry["ip"]
                is_safe = hostname.lower() in _SAFE_HOSTS
                icon = "🟢" if is_safe else "⚪"
                lines.append(f"   {icon} {ip:>15} → {hostname}")
        else:
            lines.append("   Keine aktiven Eintraege (Standard-Konfiguration)")

        # Verdaechtige Eintraege
        if suspicious:
            lines.append("")
            lines.append("⚠️  VERDAECHTIGE EINTRAEGE:")
            for s in suspicious:
                lines.append(f"   🔴 Zeile {s['line']}: {s['ip']} → {s['hostname']}")
                lines.append(f"      Grund: {s['reason']}")
        else:
            lines.append("")
            lines.append("✅ Keine verdaechtigen Eintraege gefunden")

        return "\n".join(lines)
