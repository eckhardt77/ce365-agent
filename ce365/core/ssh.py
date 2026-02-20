"""
CE365 Agent - SSH Remote Connection

SSH-Verbindungen fuer Remote-Wartung.
Nutzt asyncssh fuer pure-Python SSH (PyInstaller-kompatibel).

Pro-Feature: Erfordert "ssh_remote" Feature-Flag.
"""

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import asyncssh
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False

from ce365.core.command_runner import CommandResult


@dataclass
class SSHConfig:
    """SSH-Verbindungsparameter"""
    host: str
    port: int = 22
    username: str = "root"
    key_path: Optional[str] = None
    password: Optional[str] = None
    known_hosts: Optional[str] = None


class SSHConnection:
    """
    Einzelne SSH-Verbindung zu einem Remote-Host.

    Fuehrt Befehle remote aus und gibt CommandResult zurueck
    (kompatibel mit dem lokalen CommandRunner).
    """

    def __init__(self, config: SSHConfig):
        self.config = config
        self._conn: Optional[Any] = None
        self._connected: bool = False

    @property
    def connected(self) -> bool:
        return self._connected and self._conn is not None

    @property
    def host_display(self) -> str:
        return f"{self.config.username}@{self.config.host}:{self.config.port}"

    async def connect(self) -> bool:
        """SSH-Verbindung herstellen"""
        if not SSH_AVAILABLE:
            raise RuntimeError(
                "asyncssh nicht installiert. "
                "Installiere mit: pip install asyncssh"
            )

        try:
            connect_kwargs = {
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username,
            }

            # SSH-Key bevorzugt
            if self.config.key_path:
                key_path = Path(self.config.key_path).expanduser()
                if key_path.exists():
                    connect_kwargs["client_keys"] = [str(key_path)]
                else:
                    raise FileNotFoundError(f"SSH-Key nicht gefunden: {key_path}")

            # Password als Fallback
            if self.config.password:
                connect_kwargs["password"] = self.config.password

            # Known-Hosts Verifikation
            if self.config.known_hosts is not None:
                connect_kwargs["known_hosts"] = self.config.known_hosts or None
            else:
                # Standard: System known_hosts nutzen
                known_hosts_path = Path.home() / ".ssh" / "known_hosts"
                if known_hosts_path.exists():
                    connect_kwargs["known_hosts"] = str(known_hosts_path)
                else:
                    connect_kwargs["known_hosts"] = None

            self._conn = await asyncssh.connect(**connect_kwargs)
            self._connected = True
            return True

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"SSH-Verbindung fehlgeschlagen: {e}")

    async def run_command(
        self,
        cmd: str,
        timeout: int = 30,
    ) -> CommandResult:
        """
        Befehl remote ausfuehren.

        Args:
            cmd: Befehl als String (wird von der Remote-Shell geparst)
            timeout: Timeout in Sekunden
        """
        if not self.connected:
            return CommandResult(
                stderr="Keine SSH-Verbindung",
                returncode=-1,
                success=False,
                source="ssh",
            )

        start = time.monotonic()
        try:
            result = await asyncio.wait_for(
                self._conn.run(cmd, check=False),
                timeout=timeout,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stdout=result.stdout.strip() if result.stdout else "",
                stderr=result.stderr.strip() if result.stderr else "",
                returncode=result.returncode or 0,
                success=(result.returncode or 0) == 0,
                duration_ms=duration_ms,
                source="ssh",
            )
        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=f"SSH-Timeout nach {timeout}s",
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="ssh",
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CommandResult(
                stderr=f"SSH-Fehler: {e}",
                returncode=-1,
                success=False,
                duration_ms=duration_ms,
                source="ssh",
            )

    async def read_file(
        self,
        path: str,
        max_bytes: int = 1_048_576,
    ) -> str:
        """Datei per SFTP lesen"""
        if not self.connected:
            raise ConnectionError("Keine SSH-Verbindung")

        try:
            async with self._conn.start_sftp_client() as sftp:
                async with sftp.open(path, "r") as f:
                    content = await f.read(max_bytes)
                    if isinstance(content, bytes):
                        return content.decode("utf-8", errors="replace")
                    return content
        except Exception as e:
            raise IOError(f"SFTP-Fehler beim Lesen von '{path}': {e}")

    async def disconnect(self):
        """SSH-Verbindung trennen"""
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None
        self._connected = False


class SSHConnectionManager:
    """
    Verwaltet die aktive SSH-Verbindung.
    Nur eine Verbindung gleichzeitig (Single-Target Modus).
    """

    def __init__(self):
        self._active: Optional[SSHConnection] = None

    @property
    def is_connected(self) -> bool:
        return self._active is not None and self._active.connected

    @property
    def active_connection(self) -> Optional[SSHConnection]:
        return self._active

    @property
    def host_display(self) -> str:
        if self._active:
            return self._active.host_display
        return ""

    async def connect(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        key_path: Optional[str] = None,
        password: Optional[str] = None,
    ) -> SSHConnection:
        """
        Neue SSH-Verbindung herstellen.
        Trennt eine bestehende Verbindung automatisch.
        """
        # Bestehende Verbindung trennen
        if self._active and self._active.connected:
            await self._active.disconnect()

        config = SSHConfig(
            host=host,
            port=port,
            username=username,
            key_path=key_path,
            password=password,
        )

        conn = SSHConnection(config)
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
            return {"connected": False}

        return {
            "connected": self._active.connected,
            "host": self._active.config.host,
            "port": self._active.config.port,
            "username": self._active.config.username,
        }
