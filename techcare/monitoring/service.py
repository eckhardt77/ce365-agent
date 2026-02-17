"""
TechCare Bot - Windows Service Wrapper für Monitoring Sensor

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under MIT License

Installiert TechCare Sensor als Windows Service / macOS LaunchDaemon
"""

import platform
import sys
from pathlib import Path


def install_windows_service():
    """
    Installiert TechCare Sensor als Windows Service

    Verwendet pywin32 (win32serviceutil)
    """
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
        import socket

        class TechCareSensorService(win32serviceutil.ServiceFramework):
            _svc_name_ = "TechCareSensor"
            _svc_display_name_ = "TechCare System Monitoring Sensor"
            _svc_description_ = "Überwacht System-Metriken und sendet sie an TechCare Backend"

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
                from techcare.monitoring.sensor import SystemSensor
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
            servicemanager.PrepareToHostSingle(TechCareSensorService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(TechCareSensorService)

        print("✅ Windows Service installiert!")
        print()
        print("Service starten: sc start TechCareSensor")
        print("Service stoppen: sc stop TechCareSensor")
        print("Service entfernen: sc delete TechCareSensor")

    except ImportError:
        print("❌ pywin32 nicht installiert!")
        print("   Installiere mit: pip install pywin32")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")


def install_macos_launchdaemon():
    """
    Installiert TechCare Sensor als macOS LaunchDaemon

    Erstellt plist in /Library/LaunchDaemons/
    """
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.techcare.sensor</string>

    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>techcare.monitoring.sensor</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/var/log/techcare-sensor.log</string>

    <key>StandardErrorPath</key>
    <string>/var/log/techcare-sensor-error.log</string>
</dict>
</plist>
"""

    plist_path = Path("/Library/LaunchDaemons/com.techcare.sensor.plist")

    try:
        # plist schreiben (erfordert sudo)
        import subprocess

        print("⚠️  Installiere LaunchDaemon (benötigt sudo)...")
        print()

        # Temporäre Datei schreiben
        temp_plist = Path("/tmp/com.techcare.sensor.plist")
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
        print(f"Logs: /var/log/techcare-sensor.log")
        print(f"Plist: {plist_path}")
        print()
        print("Daemon starten: sudo launchctl start com.techcare.sensor")
        print("Daemon stoppen: sudo launchctl stop com.techcare.sensor")
        print("Daemon entfernen: sudo launchctl unload /Library/LaunchDaemons/com.techcare.sensor.plist")

    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Installieren: {str(e)}")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")


def install_linux_systemd():
    """
    Installiert TechCare Sensor als systemd Service (Linux)

    Erstellt service file in /etc/systemd/system/
    """
    service_content = f"""[Unit]
Description=TechCare System Monitoring Sensor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={Path.cwd()}
ExecStart={sys.executable} -m techcare.monitoring.sensor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("/etc/systemd/system/techcare-sensor.service")

    try:
        import subprocess

        print("⚠️  Installiere systemd Service (benötigt sudo)...")
        print()

        # Temporäre Datei schreiben
        temp_service = Path("/tmp/techcare-sensor.service")
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
            ["sudo", "systemctl", "enable", "techcare-sensor"],
            check=True
        )

        print("✅ systemd Service installiert!")
        print()
        print(f"Service-Datei: {service_path}")
        print()
        print("Service starten: sudo systemctl start techcare-sensor")
        print("Service stoppen: sudo systemctl stop techcare-sensor")
        print("Service-Status: sudo systemctl status techcare-sensor")
        print("Logs: sudo journalctl -u techcare-sensor -f")

    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Installieren: {str(e)}")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")


def main():
    """Main Entry für Service-Installation"""
    os_type = platform.system().lower()

    print()
    print("🔧 TechCare Sensor - Service Installation")
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
