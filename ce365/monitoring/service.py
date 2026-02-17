"""
CE365 Agent - Windows Service Wrapper für Monitoring Sensor

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Installiert CE365 Sensor als Windows Service / macOS LaunchDaemon
"""

import platform
import sys
from pathlib import Path


def install_windows_service():
    """
    Installiert CE365 Sensor als Windows Service

    Verwendet pywin32 (win32serviceutil)
    """
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
        import socket

        class CE365SensorService(win32serviceutil.ServiceFramework):
            _svc_name_ = "CE365Sensor"
            _svc_display_name_ = "CE365 System Monitoring Sensor"
            _svc_description_ = "Überwacht System-Metriken und sendet sie an CE365 Backend"

            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.stop_event = win32event.CreateEvent(None, 0, 0, None)
                socket.setdefaulttimeout(60)
                self.is_alive = True

            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                win32event.SetEvent(self.stop_event)
                self.is_alive = False

            def SvcDoRun(self):
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
                self.main()

            def main(self):
                """Service Main Loop"""
                import asyncio
                import os
                from ce365.monitoring.sensor import SystemSensor
                from dotenv import load_dotenv

                # .env laden
                load_dotenv()

                backend_url = os.getenv("BACKEND_URL")
                api_key = os.getenv("ANTHROPIC_API_KEY")
                interval = int(os.getenv("SENSOR_INTERVAL", "300"))

                # Sensor starten
                sensor = SystemSensor(
                    backend_url=backend_url,
                    api_key=api_key,
                    interval=interval
                )

                # Event Loop
                asyncio.run(sensor.run())

        # Service installieren
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(CE365SensorService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(CE365SensorService)

        print("✅ Windows Service installiert!")
        print()
        print("Service starten: sc start CE365Sensor")
        print("Service stoppen: sc stop CE365Sensor")
        print("Service entfernen: sc delete CE365Sensor")

    except ImportError:
        print("❌ pywin32 nicht installiert!")
        print("   Installiere mit: pip install pywin32")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")


def install_macos_launchdaemon():
    """
    Installiert CE365 Sensor als macOS LaunchDaemon

    Erstellt plist in /Library/LaunchDaemons/
    """
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ce365.sensor</string>

    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>ce365.monitoring.sensor</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/var/log/ce365-sensor.log</string>

    <key>StandardErrorPath</key>
    <string>/var/log/ce365-sensor-error.log</string>
</dict>
</plist>
"""

    plist_path = Path("/Library/LaunchDaemons/com.ce365.sensor.plist")

    try:
        # plist schreiben (erfordert sudo)
        import subprocess

        print("⚠️  Installiere LaunchDaemon (benötigt sudo)...")
        print()

        # Temporäre Datei schreiben
        temp_plist = Path("/tmp/com.ce365.sensor.plist")
        temp_plist.write_text(plist_content)

        # Nach LaunchDaemons kopieren
        subprocess.run(
            ["sudo", "cp", str(temp_plist), str(plist_path)],
            check=True
        )

        # Permissions setzen
        subprocess.run(
            ["sudo", "chown", "root:wheel", str(plist_path)],
            check=True
        )
        subprocess.run(
            ["sudo", "chmod", "644", str(plist_path)],
            check=True
        )

        # LaunchDaemon laden
        subprocess.run(
            ["sudo", "launchctl", "load", str(plist_path)],
            check=True
        )

        print("✅ macOS LaunchDaemon installiert!")
        print()
        print(f"Logs: /var/log/ce365-sensor.log")
        print(f"Plist: {plist_path}")
        print()
        print("Daemon starten: sudo launchctl start com.ce365.sensor")
        print("Daemon stoppen: sudo launchctl stop com.ce365.sensor")
        print("Daemon entfernen: sudo launchctl unload /Library/LaunchDaemons/com.ce365.sensor.plist")

    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Installieren: {str(e)}")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")


def install_linux_systemd():
    """
    Installiert CE365 Sensor als systemd Service (Linux)

    Erstellt service file in /etc/systemd/system/
    """
    service_content = f"""[Unit]
Description=CE365 System Monitoring Sensor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={Path.cwd()}
ExecStart={sys.executable} -m ce365.monitoring.sensor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("/etc/systemd/system/ce365-sensor.service")

    try:
        import subprocess

        print("⚠️  Installiere systemd Service (benötigt sudo)...")
        print()

        # Temporäre Datei schreiben
        temp_service = Path("/tmp/ce365-sensor.service")
        temp_service.write_text(service_content)

        # Nach systemd kopieren
        subprocess.run(
            ["sudo", "cp", str(temp_service), str(service_path)],
            check=True
        )

        # systemd reload
        subprocess.run(
            ["sudo", "systemctl", "daemon-reload"],
            check=True
        )

        # Service enablen
        subprocess.run(
            ["sudo", "systemctl", "enable", "ce365-sensor"],
            check=True
        )

        print("✅ systemd Service installiert!")
        print()
        print(f"Service-Datei: {service_path}")
        print()
        print("Service starten: sudo systemctl start ce365-sensor")
        print("Service stoppen: sudo systemctl stop ce365-sensor")
        print("Service-Status: sudo systemctl status ce365-sensor")
        print("Logs: sudo journalctl -u ce365-sensor -f")

    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Installieren: {str(e)}")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")


def main():
    """Main Entry für Service-Installation"""
    os_type = platform.system().lower()

    print()
    print("🔧 CE365 Sensor - Service Installation")
    print("=" * 50)
    print()

    if os_type == "windows":
        print("Plattform: Windows")
        print("Installiere als Windows Service...")
        print()
        install_windows_service()

    elif os_type == "darwin":
        print("Plattform: macOS")
        print("Installiere als LaunchDaemon...")
        print()
        install_macos_launchdaemon()

    elif os_type == "linux":
        print("Plattform: Linux")
        print("Installiere als systemd Service...")
        print()
        install_linux_systemd()

    else:
        print(f"❌ Plattform nicht unterstützt: {os_type}")


if __name__ == "__main__":
    main()
