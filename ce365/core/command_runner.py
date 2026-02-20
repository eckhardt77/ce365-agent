"""
CE365 Agent - Zentraler Command Runner

Einheitliche Schnittstelle fuer alle System-Befehle.
Alle Tools nutzen diesen Runner statt eigener subprocess.run() Aufrufe.
Unterstuetzt lokale und remote (SSH) Ausfuehrung.
"""

import subprocess
import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ce365.core.ssh import SSHConnection
    from ce365.core.winrm import WinRMConnection


@dataclass
class CommandResult:
    """Ergebnis eines ausgefuehrten Befehls"""
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    success: bool = False
    duration_ms: int = 0
    source: str = "local"  # "local", "ssh" oder "winrm"

    @property
    def output(self) -> str:
        """Hauptausgabe: stdout wenn vorhanden, sonst stderr"""
        return self.stdout.strip() if self.stdout.strip() else self.stderr.strip()


class CommandRunner:
    """
    Zentraler Command Runner fuer alle System-Befehle.

    Unterstuetzt drei Modi:
    - "local": subprocess.run() auf dem lokalen System
    - "remote": SSH-Ausfuehrung auf einem Remote-Host (macOS/Linux)
    - "winrm": WinRM/PowerShell Remoting auf Windows-Hosts

    Tools wissen NICHT ob sie lokal oder remote laufen.
    Der Runner routet automatisch.
    """

    def __init__(self):
        self._mode: str = "local"  # "local", "remote" (SSH), "winrm"
        self._ssh_connection: Optional["SSHConnection"] = None
        self._winrm_connection: Optional["WinRMConnection"] = None

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_remote(self) -> bool:
        if self._mode == "remote" and self._ssh_connection is not None:
            return True
        if self._mode == "winrm" and self._winrm_connection is not None:
            return True
        return False

    @property
    def transport(self) -> str:
        """Aktiver Transport: 'local', 'ssh' oder 'winrm'"""
        if self._mode == "remote":
            return "ssh"
        return self._mode

    @property
    def remote_host(self) -> str:
        """Hostname der aktiven Remote-Verbindung"""
        if self._mode == "remote" and self._ssh_connection:
            return self._ssh_connection.config.host
        if self._mode == "winrm" and self._winrm_connection:
            return self._winrm_connection.config.host
        return ""

    def set_remote(self, ssh_connection: "SSHConnection"):
        """Auf SSH Remote-Modus umschalten"""
        self._ssh_connection = ssh_connection
        self._winrm_connection = None
        self._mode = "remote"

    def set_winrm(self, winrm_connection: "WinRMConnection"):
        """Auf WinRM-Modus umschalten"""
        self._winrm_connection = winrm_connection
        self._ssh_connection = None
        self._mode = "winrm"

    def set_local(self):
        """Auf lokalen Modus zurueckschalten"""
        self._ssh_connection = None
        self._winrm_connection = None
        self._mode = "local"

    # ============================================================
    # Command Execution
    # ============================================================

    def run_sync(
        self,
        cmd: list,
        timeout: int = 30,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Befehl synchron ausfuehren (immer lokal).
        Fuer Legacy-Kompatibilitaet — neue Tools sollten run() nutzen.
        """
        return self._run_local(cmd, timeout=timeout, cwd=cwd)

    async def run(
        self,
        cmd: list,
        timeout: int = 30,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """
        Befehl ausfuehren — routet automatisch lokal/SSH/WinRM.
        """
        if self._mode == "remote" and self._ssh_connection:
            return await self._run_remote(cmd, timeout=timeout)
        if self._mode == "winrm" and self._winrm_connection:
            return await self._run_winrm(cmd, timeout=timeout)
        return self._run_local(cmd, timeout=timeout, cwd=cwd)

    def _run_local(
        self,
        cmd: list,
        timeout: int = 30,
        cwd: Optional[str] = None,
    ) -> CommandResult:
        """Befehl lokal ausfuehren via subprocess"""
        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                returncode=result.returncode,
                success=result.returncode == 0,
                duration_ms=duration_ms,
                source="local",
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=f"Timeout nach {timeout}s",
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="local",
            )
        except FileNotFoundError:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=f"Befehl nicht gefunden: {cmd[0]}",
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="local",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=str(e),
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="local",
            )

    async def _run_remote(
        self,
        cmd: list,
        timeout: int = 30,
    ) -> CommandResult:
        """Befehl remote via SSH ausfuehren"""
        if not self._ssh_connection or not self._ssh_connection.connected:
            return CommandResult(
                stderr="Keine SSH-Verbindung aktiv",
                returncode=-1,
                success=False,
                source="ssh",
            )
        # Liste zu Shell-String konvertieren (Quoting)
        import shlex
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        return await self._ssh_connection.run_command(cmd_str, timeout=timeout)

    async def _run_winrm(
        self,
        cmd: list,
        timeout: int = 30,
    ) -> CommandResult:
        """Befehl remote via WinRM/PowerShell ausfuehren"""
        if not self._winrm_connection or not self._winrm_connection.connected:
            return CommandResult(
                stderr="Keine WinRM-Verbindung aktiv",
                returncode=-1,
                success=False,
                source="winrm",
            )
        # Liste zu String konvertieren
        cmd_str = " ".join(cmd)
        return await self._winrm_connection.run_command(cmd_str, timeout=timeout)

    # ============================================================
    # File Operations (lokal oder remote)
    # ============================================================

    async def read_file(
        self,
        path: str,
        max_lines: int = 200,
    ) -> CommandResult:
        """Datei lesen — lokal, per SSH/SFTP oder per WinRM"""
        if self._mode == "remote" and self._ssh_connection:
            return await self._read_file_remote(path, max_lines)
        if self._mode == "winrm" and self._winrm_connection:
            return await self._read_file_winrm(path, max_lines)
        return self._read_file_local(path, max_lines)

    def _read_file_local(self, path: str, max_lines: int) -> CommandResult:
        """Datei lokal lesen"""
        start = time.monotonic()
        try:
            from pathlib import Path as _Path
            p = _Path(path)
            content = p.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            truncated = lines[:max_lines]
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout="\n".join(truncated),
                returncode=0,
                success=True,
                duration_ms=duration_ms,
                source="local",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=str(e),
                returncode=1,
                success=False,
                duration_ms=duration_ms,
                source="local",
            )

    async def _read_file_remote(self, path: str, max_lines: int) -> CommandResult:
        """Datei per SSH/SFTP lesen"""
        start = time.monotonic()
        try:
            content = await self._ssh_connection.read_file(path)
            lines = content.splitlines()
            truncated = lines[:max_lines]
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout="\n".join(truncated),
                returncode=0,
                success=True,
                duration_ms=duration_ms,
                source="ssh",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=str(e),
                returncode=1,
                success=False,
                duration_ms=duration_ms,
                source="ssh",
            )

    async def _read_file_winrm(self, path: str, max_lines: int) -> CommandResult:
        """Datei per WinRM/PowerShell lesen"""
        start = time.monotonic()
        try:
            content = await self._winrm_connection.read_file(path)
            lines = content.splitlines()
            truncated = lines[:max_lines]
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout="\n".join(truncated),
                returncode=0,
                success=True,
                duration_ms=duration_ms,
                source="winrm",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=str(e),
                returncode=1,
                success=False,
                duration_ms=duration_ms,
                source="winrm",
            )

    async def search_file(
        self,
        path: str,
        pattern: str,
        max_results: int = 50,
    ) -> CommandResult:
        """In Datei suchen — lokal, per SSH grep oder per WinRM Select-String"""
        if self._mode == "remote" and self._ssh_connection:
            import shlex
            cmd_str = f"grep -n -i -m {max_results} {shlex.quote(pattern)} {shlex.quote(path)}"
            return await self._ssh_connection.run_command(cmd_str, timeout=30)
        if self._mode == "winrm" and self._winrm_connection:
            escaped_path = path.replace("'", "''")
            escaped_pattern = pattern.replace("'", "''")
            ps_cmd = (
                f"Select-String -Path '{escaped_path}' -Pattern '{escaped_pattern}' "
                f"-CaseSensitive:$false | Select-Object -First {max_results} | "
                f"ForEach-Object {{ \"$($_.LineNumber): $($_.Line)\" }}"
            )
            return await self._winrm_connection.run_command(ps_cmd, timeout=30)
        return self._search_file_local(path, pattern, max_results)

    def _search_file_local(self, path: str, pattern: str, max_results: int) -> CommandResult:
        """In lokaler Datei suchen"""
        import re
        start = time.monotonic()
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            matches = []
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append(f"{line_num}: {line.rstrip()}")
                        if len(matches) >= max_results:
                            break
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout="\n".join(matches),
                returncode=0,
                success=True,
                duration_ms=duration_ms,
                source="local",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=str(e),
                returncode=1,
                success=False,
                duration_ms=duration_ms,
                source="local",
            )


# ============================================================
# Singleton
# ============================================================

_runner_instance: Optional[CommandRunner] = None


def get_command_runner() -> CommandRunner:
    """Singleton-Zugriff auf den Command Runner"""
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = CommandRunner()
    return _runner_instance
