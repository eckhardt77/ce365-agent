"""
CE365 Agent - Process Manager

Prozesse per Name oder PID beenden
Plattformuebergreifend via psutil
"""

import psutil
from typing import Dict, Any
from ce365.tools.base import RepairTool


class KillProcessTool(RepairTool):
    """Prozess per Name oder PID beenden"""

    @property
    def name(self) -> str:
        return "kill_process"

    @property
    def description(self) -> str:
        return (
            "Beendet einen Prozess per Name oder PID. "
            "Nutze dies bei: 1) Hängende/eingefrorene Programme, "
            "2) Prozesse die zu viel CPU/RAM verbrauchen, "
            "3) Nicht reagierende Anwendungen. "
            "Versucht zuerst sanftes Beenden (terminate), dann hartes Beenden (kill). "
            "Erfordert GO REPAIR!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "process_name": {
                    "type": "string",
                    "description": "Prozess-Name (z.B. 'chrome', 'firefox', 'Teams'). Beendet ALLE Prozesse mit diesem Namen.",
                },
                "pid": {
                    "type": "integer",
                    "description": "Prozess-ID (PID). Beendet nur diesen spezifischen Prozess.",
                },
                "force": {
                    "type": "boolean",
                    "description": "Sofort hartes Beenden (kill) statt sanftes Beenden (terminate)",
                    "default": False,
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs) -> str:
        process_name = kwargs.get("process_name", "")
        pid = kwargs.get("pid", None)
        force = kwargs.get("force", False)

        if not process_name and pid is None:
            return "❌ Bitte process_name oder pid angeben"

        lines = []

        if pid is not None:
            # Einzelnen Prozess per PID beenden
            lines.extend(self._kill_by_pid(pid, force))
        else:
            # Alle Prozesse mit dem Namen beenden
            lines.extend(self._kill_by_name(process_name, force))

        return "\n".join(lines)

    def _kill_by_pid(self, pid: int, force: bool) -> list:
        lines = []
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc_cpu = proc.cpu_percent(interval=0.1)
            proc_mem = proc.memory_info().rss / (1024 * 1024)

            lines.append(f"🔧 Beende Prozess: {proc_name} (PID: {pid})")
            lines.append(f"   CPU: {proc_cpu:.1f}% | RAM: {proc_mem:.1f} MB")
            lines.append("")

            if force:
                proc.kill()
                lines.append(f"✅ Prozess {proc_name} (PID: {pid}) wurde gekillt (force)")
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    lines.append(f"✅ Prozess {proc_name} (PID: {pid}) wurde beendet")
                except psutil.TimeoutExpired:
                    proc.kill()
                    lines.append(f"⚠️  Prozess reagierte nicht — wurde gekillt (force)")

        except psutil.NoSuchProcess:
            lines.append(f"❌ Prozess mit PID {pid} existiert nicht")
        except psutil.AccessDenied:
            lines.append(f"❌ Keine Berechtigung zum Beenden von PID {pid}")
            lines.append("   → Erhoehte Rechte (Admin/sudo) erforderlich")
        except Exception as e:
            lines.append(f"❌ Fehler: {e}")

        return lines

    def _kill_by_name(self, name: str, force: bool) -> list:
        lines = []
        name_lower = name.lower()

        # Alle passenden Prozesse finden
        matching = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if name_lower in proc.info["name"].lower():
                    matching.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not matching:
            lines.append(f"❌ Kein Prozess mit Name '{name}' gefunden")
            # Aehnliche vorschlagen
            suggestions = set()
            for proc in psutil.process_iter(["name"]):
                try:
                    pname = proc.info["name"]
                    if any(c in pname.lower() for c in name_lower[:3]):
                        suggestions.add(pname)
                except:
                    pass
            if suggestions:
                lines.append(f"   Meinten Sie: {', '.join(sorted(suggestions)[:5])}")
            return lines

        lines.append(f"🔧 Beende {len(matching)} Prozess(e) mit Name '{name}':")
        lines.append("")

        killed = 0
        failed = 0

        for proc in matching:
            try:
                pid = proc.pid
                pname = proc.name()

                if force:
                    proc.kill()
                else:
                    proc.terminate()

                lines.append(f"   ✅ {pname} (PID: {pid}) beendet")
                killed += 1
            except psutil.AccessDenied:
                lines.append(f"   ❌ {proc.name()} (PID: {proc.pid}) — Keine Berechtigung")
                failed += 1
            except psutil.NoSuchProcess:
                pass  # Bereits beendet
            except Exception as e:
                lines.append(f"   ❌ PID {proc.pid} — Fehler: {e}")
                failed += 1

        # Warten auf terminate (wenn nicht force)
        if not force and killed > 0:
            gone, alive = psutil.wait_procs(
                [p for p in matching if p.is_running()],
                timeout=5,
            )
            for p in alive:
                try:
                    p.kill()
                    lines.append(f"   ⚠️  {p.name()} (PID: {p.pid}) musste gekillt werden")
                except:
                    pass

        lines.append("")
        lines.append(f"Ergebnis: {killed} beendet, {failed} fehlgeschlagen")

        return lines
