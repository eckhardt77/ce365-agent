"""
CE365 Agent - WinRM Remote Connection

PowerShell Remoting via WinRM fuer Windows-Fernwartung.
Nutzt pypsrp (pure-Python, PyInstaller-kompatibel).

Voraussetzungen auf dem Ziel-Windows:
- WinRM aktiviert: Enable-PSRemoting -Force
- HTTPS empfohlen: winrm quickconfig -transport:https
- Firewall: Port 5985 (HTTP) oder 5986 (HTTPS)

Pro-Feature: Erfordert "ssh_remote" Feature-Flag.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    from pypsrp.client import Client as PSRPClient
    WINRM_AVAILABLE = True
except ImportError:
    WINRM_AVAILABLE = False

from ce365.core.command_runner import CommandResult


@dataclass
class WinRMConfig:
    """WinRM-Verbindungsparameter"""
    host: str
    port: int = 5985
    username: str = "Administrator"
    password: str = ""
    ssl: bool = False
    verify_ssl: bool = True


class WinRMConnection:
    """
    WinRM-Verbindung zu einem Windows-Host.

    Fuehrt PowerShell-Befehle remote aus und gibt CommandResult zurueck
    (kompatibel mit dem lokalen CommandRunner).
    """

    def __init__(self, config: WinRMConfig):
        self.config = config
        self._client: Optional[Any] = None
        self._connected: bool = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def host_display(self) -> str:
        proto = "https" if self.config.ssl else "http"
        return f"{self.config.username}@{self.config.host}:{self.config.port} ({proto})"

    async def connect(self) -> bool:
        """WinRM-Verbindung herstellen und testen"""
        if not WINRM_AVAILABLE:
            raise RuntimeError(
                "pypsrp nicht installiert. "
                "Installiere mit: pip install pypsrp"
            )

        try:
            self._client = PSRPClient(
                server=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                ssl=self.config.ssl,
                cert_validation=self.config.verify_ssl,
            )

            # Verbindung testen mit simplem Befehl
            test_result = await self._run_powershell("$env:COMPUTERNAME")
            if test_result.success:
                self._connected = True
                return True
            else:
                raise ConnectionError(
                    f"WinRM-Verbindungstest fehlgeschlagen: {test_result.stderr}"
                )

        except Exception as e:
            self._connected = False
            if "pypsrp" in str(type(e).__module__):
                raise ConnectionError(f"WinRM-Verbindung fehlgeschlagen: {e}")
            raise

    async def _run_powershell(self, script: str, timeout: int = 30) -> CommandResult:
        """PowerShell-Script remote ausfuehren"""
        start = time.monotonic()
        try:
            # pypsrp ist synchron — in Thread ausfuehren
            loop = asyncio.get_event_loop()
            stdout, stderr, had_errors = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._execute_ps_sync,
                    script,
                ),
                timeout=timeout,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout=stdout.strip() if stdout else "",
                stderr=stderr.strip() if stderr else "",
                returncode=1 if had_errors else 0,
                success=not had_errors,
                duration_ms=duration_ms,
                source="winrm",
            )
        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=f"WinRM-Timeout nach {timeout}s",
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="winrm",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=f"WinRM-Fehler: {e}",
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="winrm",
            )

    def _execute_ps_sync(self, script: str) -> tuple:
        """Synchroner PowerShell-Aufruf (wird in Thread ausgefuehrt)"""
        output, streams, had_errors = self._client.execute_ps(script)
        stderr = ""
        if streams and streams.error:
            stderr = "\n".join(str(e) for e in streams.error)
        return output, stderr, had_errors

    async def run_command(
        self,
        cmd: str,
        timeout: int = 30,
    ) -> CommandResult:
        """
        Befehl remote ausfuehren.

        Erkennt automatisch ob cmd ein PowerShell-Befehl oder ein
        klassischer Windows-Befehl ist und wrapped entsprechend.
        """
        if not self.connected:
            return CommandResult(
                stderr="Keine WinRM-Verbindung",
                returncode=-1,
                success=False,
                source="winrm",
            )

        # Klassische CMD-Befehle in PowerShell wrappen
        # z.B. "net stop wuauserv" → "cmd /c 'net stop wuauserv'"
        ps_script = self._to_powershell(cmd)
        return await self._run_powershell(ps_script, timeout=timeout)

    def _to_powershell(self, cmd: str) -> str:
        """
        Konvertiert einen Shell-Befehl in PowerShell.

        Strategie:
        - Wenn der Befehl PowerShell-typisch ist, direkt ausfuehren
        - Wenn es ein klassischer CMD-Befehl ist, via cmd /c wrappen
        """
        cmd = cmd.strip()

        # Bereits PowerShell-Syntax erkennen
        ps_indicators = [
            "$", "Get-", "Set-", "New-", "Remove-", "Invoke-",
            "Start-", "Stop-", "Restart-", "Enable-", "Disable-",
            "Test-", "Select-", "Where-Object", "ForEach-Object",
            "|", "Write-", "Import-", "Export-",
        ]
        for indicator in ps_indicators:
            if indicator in cmd:
                return cmd

        # CMD-Befehle erkennen und wrappen
        cmd_programs = [
            "net ", "sc ", "reg ", "wmic ", "ipconfig", "ping ",
            "tracert", "nslookup", "netsh ", "sfc ", "dism ",
            "chkdsk", "defrag", "schtasks", "tasklist", "taskkill",
            "regsvr32", "bcdedit", "diskpart", "format", "robocopy",
            "attrib", "icacls", "certutil", "systeminfo", "hostname",
            "whoami", "gpupdate", "gpresult", "shutdown",
        ]
        cmd_lower = cmd.lower()
        for prog in cmd_programs:
            if cmd_lower.startswith(prog):
                # Quoting fuer PowerShell: Einfache Anfuehrungszeichen
                escaped = cmd.replace("'", "''")
                return f"cmd /c '{escaped}'"

        # Fallback: Als PowerShell ausfuehren
        return cmd

    async def read_file(
        self,
        path: str,
        max_bytes: int = 1_048_576,
    ) -> str:
        """Datei per WinRM/PowerShell lesen"""
        if not self.connected:
            raise ConnectionError("Keine WinRM-Verbindung")

        # PowerShell: Datei lesen mit Groessenlimit
        escaped_path = path.replace("'", "''")
        ps_script = f"""
$f = '{escaped_path}'
if (Test-Path $f) {{
    $size = (Get-Item $f).Length
    if ($size -gt {max_bytes}) {{
        Write-Error "Datei zu gross: $size Bytes (Max: {max_bytes})"
    }} else {{
        Get-Content $f -Raw -Encoding UTF8
    }}
}} else {{
    Write-Error "Datei nicht gefunden: $f"
}}
"""
        result = await self._run_powershell(ps_script.strip(), timeout=30)
        if result.success:
            return result.stdout
        else:
            raise IOError(f"WinRM-Fehler beim Lesen: {result.stderr}")

    async def disconnect(self):
        """WinRM-Verbindung trennen"""
        self._client = None
        self._connected = False


class WinRMConnectionManager:
    """
    Verwaltet die aktive WinRM-Verbindung.
    Nur eine Verbindung gleichzeitig (Single-Target Modus).
    """

    def __init__(self):
        self._active: Optional[WinRMConnection] = None

    @property
    def is_connected(self) -> bool:
        return self._active is not None and self._active.connected

    @property
    def active_connection(self) -> Optional[WinRMConnection]:
        return self._active

    @property
    def host_display(self) -> str:
        if self._active:
            return self._active.host_display
        return ""

    async def connect(
        self,
        host: str,
        port: int = 5985,
        username: str = "Administrator",
        password: str = "",
        ssl: bool = False,
        verify_ssl: bool = True,
    ) -> WinRMConnection:
        """
        Neue WinRM-Verbindung herstellen.
        Trennt eine bestehende Verbindung automatisch.
        """
        if self._active and self._active.connected:
            await self._active.disconnect()

        config = WinRMConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            ssl=ssl,
            verify_ssl=verify_ssl,
        )

        conn = WinRMConnection(config)
        await conn.connect()
        self._active = conn
        return conn

    async def disconnect(self):
        """Aktive Verbindung trennen"""
        if self._active:
            await self._active.disconnect()
            self._active = None

    def get_status(self) -> Dict[str, Any]:
        """Verbindungsstatus"""
        if not self._active:
            return {"connected": False, "transport": "winrm"}

        return {
            "connected": self._active.connected,
            "transport": "winrm",
            "host": self._active.config.host,
            "port": self._active.config.port,
            "username": self._active.config.username,
            "ssl": self._active.config.ssl,
        }
