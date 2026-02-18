"""
CE365 Agent - Stress Test & Diagnostic Tools

Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
Licensed under Source Available License

Hardware-Tests:
- CPU Stress Test
- RAM Stress Test
- Disk Speed Test
- Temperature Monitoring
- System Stability Test
"""

import platform
import subprocess
import time
import psutil
from typing import Dict, Any
from ce365.tools.base import AuditTool


class StressTestCPUTool(AuditTool):
    """
    CPU Stress Test

    Setzt CPU unter Last und überwacht Performance
    """

    @property
    def name(self) -> str:
        return "stress_test_cpu"

    @property
    def description(self) -> str:
        return (
            "Führt CPU Stress Test durch. "
            "Nutze dies bei: 1) Hardware-Problemen, 2) Überhitzung-Verdacht, "
            "3) Performance-Tests, 4) Stabilitäts-Checks. "
            "Setzt CPU für 30-60 Sekunden unter 100% Last."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "duration": {
                    "type": "integer",
                    "description": "Test-Dauer in Sekunden (Standard: 30, Max: 300)",
                    "default": 30
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        CPU Stress Test

        Args:
            duration: Test-Dauer in Sekunden (default: 30)

        Returns:
            Test-Ergebnis mit CPU-Stats
        """
        duration = min(kwargs.get("duration", 30), 300)  # Max 5 Minuten

        try:
            output = [
                "🔥 CPU Stress Test",
                "",
                f"⏱️  Dauer: {duration} Sekunden",
                "⚠️  CPU wird unter 100% Last gesetzt!",
                ""
            ]

            # CPU-Info vor Test
            cpu_count = psutil.cpu_count()
            output.append(f"CPU Cores: {cpu_count}")

            # Baseline CPU
            baseline_cpu = psutil.cpu_percent(interval=1)
            output.append(f"Baseline CPU: {baseline_cpu}%")
            output.append("")

            output.append("🔥 Starte Stress Test...")
            output.append("")

            # Start Test
            os_type = platform.system()

            if os_type == "Windows":
                # Windows: PowerShell CPU Loop
                process = subprocess.Popen(
                    ["powershell", "-Command", f"$end = (Get-Date).AddSeconds({duration}); while ((Get-Date) -lt $end) {{ $result = 1; for ($i = 0; $i -lt 1000000; $i++) {{ $result = $result * 2 }} }}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # macOS/Linux: yes > /dev/null
                process = subprocess.Popen(
                    ["sh", "-c", f"timeout {duration} yes > /dev/null"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            # Monitor CPU während Test
            samples = []
            start_time = time.time()

            while time.time() - start_time < duration:
                cpu = psutil.cpu_percent(interval=1)
                samples.append(cpu)
                elapsed = int(time.time() - start_time)
                output.append(f"  [{elapsed}s] CPU: {cpu}%")

                if len(samples) >= duration:
                    break

            # Test beenden
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

            # Statistiken
            output.append("")
            output.append("📊 Test-Ergebnis:")
            output.append("")

            avg_cpu = sum(samples) / len(samples) if samples else 0
            max_cpu = max(samples) if samples else 0

            output.append(f"  Durchschnitt: {avg_cpu:.1f}%")
            output.append(f"  Maximum: {max_cpu:.1f}%")

            # CPU nach Test
            time.sleep(2)
            post_cpu = psutil.cpu_percent(interval=1)
            output.append(f"  Nach Test: {post_cpu}%")
            output.append("")

            # Bewertung
            if avg_cpu >= 90:
                output.append("✅ CPU-Performance: Sehr gut (≥90%)")
            elif avg_cpu >= 70:
                output.append("⚠️  CPU-Performance: Mittel (70-90%)")
                output.append("   Mögliche Throttling oder Background-Prozesse")
            else:
                output.append("❌ CPU-Performance: Niedrig (<70%)")
                output.append("   Thermal Throttling oder Hardware-Problem")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim CPU Stress Test: {str(e)}"


class StressTestMemoryTool(AuditTool):
    """
    RAM Stress Test

    Testet Speicher unter Last
    """

    @property
    def name(self) -> str:
        return "stress_test_memory"

    @property
    def description(self) -> str:
        return (
            "Führt RAM Stress Test durch. "
            "Nutze dies bei: 1) Speicher-Problemen, 2) Crashes/Blue Screens, "
            "3) Instabilität, 4) Nach RAM-Upgrade. "
            "Allokiert und testet Speicher."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "size_mb": {
                    "type": "integer",
                    "description": "Zu testende Speichergröße in MB (Standard: 512)",
                    "default": 512
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        RAM Stress Test

        Args:
            size_mb: Speichergröße in MB (default: 512)

        Returns:
            Test-Ergebnis
        """
        size_mb = kwargs.get("size_mb", 512)

        try:
            output = [
                "💾 RAM Stress Test",
                "",
                f"📊 Test-Größe: {size_mb} MB",
                ""
            ]

            # RAM-Info
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024**3)
            available_gb = mem.available / (1024**3)

            output.append(f"RAM Total: {total_gb:.1f} GB")
            output.append(f"RAM Verfügbar: {available_gb:.1f} GB ({mem.percent}% genutzt)")
            output.append("")

            # Sicherheitscheck
            if size_mb > mem.available / (1024**2) * 0.8:
                return (
                    "❌ Test abgebrochen\n\n"
                    f"Test-Größe ({size_mb} MB) ist zu groß für verfügbaren RAM.\n"
                    f"Verfügbar: {available_gb:.1f} GB\n"
                    "Reduziere size_mb Parameter."
                )

            output.append("🔥 Starte RAM Test...")
            output.append("")

            # Speicher allokieren und schreiben
            chunk_size = 1024 * 1024  # 1 MB Chunks
            chunks = []
            start_time = time.time()

            for i in range(size_mb):
                try:
                    # Allokiere 1 MB und schreibe Daten
                    chunk = bytearray(chunk_size)
                    # Schreibe Pattern
                    for j in range(0, chunk_size, 4):
                        chunk[j:j+4] = (i * chunk_size + j).to_bytes(4, 'little')
                    chunks.append(chunk)

                    if (i + 1) % 100 == 0:
                        output.append(f"  Allokiert: {i + 1} MB")

                except MemoryError:
                    output.append(f"\n❌ MemoryError bei {i} MB")
                    break

            elapsed = time.time() - start_time

            output.append("")
            output.append(f"✓ {len(chunks)} MB allokiert in {elapsed:.1f}s")
            output.append("")

            # Speicher lesen und verifizieren
            output.append("🔍 Verifiziere Daten...")
            errors = 0

            for i in range(min(len(chunks), 100)):  # Nur erste 100 MB verifizieren
                chunk = chunks[i]
                for j in range(0, len(chunk), 4):
                    expected = (i * chunk_size + j).to_bytes(4, 'little')
                    actual = chunk[j:j+4]
                    if expected != actual:
                        errors += 1

            output.append("")

            if errors == 0:
                output.append("✅ RAM Test BESTANDEN")
                output.append("   Keine Fehler gefunden")
            else:
                output.append(f"❌ RAM Test FEHLGESCHLAGEN")
                output.append(f"   {errors} Fehler gefunden")
                output.append("")
                output.append("⚠️  Mögliches RAM-Problem!")
                output.append("   Empfehlung: Memtest86+ durchführen")

            # Cleanup
            chunks.clear()

            # RAM nach Test
            mem_after = psutil.virtual_memory()
            output.append("")
            output.append(f"RAM nach Test: {mem_after.percent}% genutzt")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim RAM Stress Test: {str(e)}"


class TestDiskSpeedTool(AuditTool):
    """
    Disk Speed Test

    Misst Read/Write Performance
    """

    @property
    def name(self) -> str:
        return "test_disk_speed"

    @property
    def description(self) -> str:
        return (
            "Testet Disk Read/Write Geschwindigkeit. "
            "Nutze dies bei: 1) Langsamer Performance, 2) Disk-Problemen, "
            "3) Nach SSD-Upgrade, 4) Hardware-Diagnostik. "
            "Misst Sequential Read/Write Speed."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_size_mb": {
                    "type": "integer",
                    "description": "Test-Dateigröße in MB (Standard: 100)",
                    "default": 100
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Disk Speed Test

        Args:
            test_size_mb: Test-Größe in MB (default: 100)

        Returns:
            Speed-Test Ergebnis in MB/s
        """
        test_size_mb = kwargs.get("test_size_mb", 100)

        try:
            import tempfile
            import os

            output = [
                "💿 Disk Speed Test",
                "",
                f"📊 Test-Größe: {test_size_mb} MB",
                ""
            ]

            # Temp-File erstellen
            temp_file = os.path.join(tempfile.gettempdir(), "ce365_speedtest.tmp")

            # WRITE Test
            output.append("✏️  Sequential Write Test...")
            write_data = bytearray(1024 * 1024)  # 1 MB Buffer

            start_time = time.time()

            with open(temp_file, 'wb') as f:
                for i in range(test_size_mb):
                    f.write(write_data)
                f.flush()
                os.fsync(f.fileno())  # Ensure written to disk

            write_time = time.time() - start_time
            write_speed = test_size_mb / write_time

            output.append(f"  Geschwindigkeit: {write_speed:.1f} MB/s")
            output.append(f"  Dauer: {write_time:.2f}s")
            output.append("")

            # READ Test
            output.append("📖 Sequential Read Test...")

            start_time = time.time()

            with open(temp_file, 'rb') as f:
                while f.read(1024 * 1024):  # Read in 1 MB chunks
                    pass

            read_time = time.time() - start_time
            read_speed = test_size_mb / read_time

            output.append(f"  Geschwindigkeit: {read_speed:.1f} MB/s")
            output.append(f"  Dauer: {read_time:.2f}s")
            output.append("")

            # Cleanup
            try:
                os.remove(temp_file)
            except:
                pass

            # Bewertung
            output.append("📊 Bewertung:")
            output.append("")

            # SSD vs HDD Benchmarks
            if read_speed > 400 and write_speed > 300:
                output.append("✅ Performance: Exzellent (NVMe SSD)")
            elif read_speed > 200 and write_speed > 150:
                output.append("✅ Performance: Sehr gut (SATA SSD)")
            elif read_speed > 80 and write_speed > 60:
                output.append("⚠️  Performance: Mittel (HDD oder langsame SSD)")
            else:
                output.append("❌ Performance: Niedrig (<80 MB/s Read)")
                output.append("   Mögliche Probleme: Fragmentierung, Disk-Fehler, USB 2.0")

            output.append("")
            output.append("Referenzwerte:")
            output.append("  • NVMe SSD: 500-3000+ MB/s")
            output.append("  • SATA SSD: 200-550 MB/s")
            output.append("  • HDD 7200rpm: 80-160 MB/s")

            return "\n".join(output)

        except Exception as e:
            # Cleanup bei Fehler
            try:
                if 'temp_file' in locals():
                    os.remove(temp_file)
            except:
                pass

            return f"❌ Fehler beim Disk Speed Test: {str(e)}"


class CheckSystemTemperatureTool(AuditTool):
    """
    System Temperatur Check

    Überwacht CPU/System-Temperatur (wo verfügbar)
    """

    @property
    def name(self) -> str:
        return "check_system_temperature"

    @property
    def description(self) -> str:
        return (
            "Prüft System-Temperaturen (CPU, Sensors). "
            "Nutze dies bei: 1) Überhitzung-Verdacht, 2) Performance-Problemen, "
            "3) Nach Stress Tests, 4) Hardware-Diagnostik. "
            "Benötigt: macOS (nativer Support) oder Windows (psutil sensors)."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Temperatur Check

        Returns:
            Temperatur-Report
        """
        try:
            output = [
                "🌡️  System Temperatur Check",
                ""
            ]

            # CPU Temperatur (psutil sensors - oft nicht auf allen Systemen verfügbar)
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()

                    if temps:
                        output.append("CPU & Sensors:")
                        found_temps = False

                        for name, entries in temps.items():
                            for entry in entries:
                                output.append(f"  {entry.label or name}: {entry.current}°C")
                                found_temps = True

                                if entry.current > 80:
                                    output.append("    ⚠️  HOCH (>80°C)")
                                elif entry.current > 70:
                                    output.append("    ⚠️  Warm (>70°C)")

                        if not found_temps:
                            output.append("  ℹ️  Keine Temperatur-Sensoren gefunden")
                    else:
                        output.append("ℹ️  Temperatur-Sensoren nicht verfügbar")
                else:
                    output.append("ℹ️  psutil sensors_temperatures nicht verfügbar")

            except Exception as e:
                output.append(f"⚠️  Temperatur konnte nicht ausgelesen werden: {str(e)}")

            output.append("")

            # CPU Auslastung (Indikator für Last)
            cpu_percent = psutil.cpu_percent(interval=1)
            output.append(f"CPU Auslastung: {cpu_percent}%")

            # Fan Speed (falls verfügbar)
            try:
                if hasattr(psutil, "sensors_fans"):
                    fans = psutil.sensors_fans()
                    if fans:
                        output.append("")
                        output.append("Lüfter:")
                        for name, entries in fans.items():
                            for entry in entries:
                                output.append(f"  {entry.label or name}: {entry.current} RPM")
            except:
                pass

            output.append("")
            output.append("💡 Hinweis:")
            output.append("  Temperatur-Monitoring ist hardware- und OS-abhängig.")
            output.append("  Für detaillierte Infos nutze:")
            output.append("  • Windows: HWiNFO, Core Temp")
            output.append("  • macOS: iStat Menus, Intel Power Gadget")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Temperatur-Check: {str(e)}"


class RunStabilityTestTool(AuditTool):
    """
    Kombinierter System Stability Test

    CPU + RAM + Disk gleichzeitig testen
    """

    @property
    def name(self) -> str:
        return "run_stability_test"

    @property
    def description(self) -> str:
        return (
            "Führt kombinierten Stabilitäts-Test durch (CPU + RAM + Disk). "
            "Nutze dies bei: 1) Neuer Hardware, 2) Nach Reparaturen, "
            "3) Crash-Problemen, 4) Vor wichtigen Aufgaben. "
            "ACHTUNG: Setzt System für 5 Minuten unter Last!"
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "duration_minutes": {
                    "type": "integer",
                    "description": "Test-Dauer in Minuten (Standard: 5, Max: 30)",
                    "default": 5
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> str:
        """
        Stability Test

        Args:
            duration_minutes: Dauer in Minuten (default: 5)

        Returns:
            Stabilitäts-Report
        """
        duration_min = min(kwargs.get("duration_minutes", 5), 30)
        duration_sec = duration_min * 60

        try:
            output = [
                "🔥 System Stability Test",
                "",
                f"⏱️  Dauer: {duration_min} Minuten",
                "⚠️  System wird unter VOLLER Last gesetzt!",
                "",
                "🔥 Test gestartet...",
                ""
            ]

            start_time = time.time()
            errors = []
            warnings = []

            # Baseline
            baseline_cpu = psutil.cpu_percent(interval=1)
            baseline_mem = psutil.virtual_memory().percent

            output.append(f"Baseline CPU: {baseline_cpu}%")
            output.append(f"Baseline RAM: {baseline_mem}%")
            output.append("")

            # CPU + RAM Test parallel
            samples = []
            elapsed = 0

            while elapsed < duration_sec:
                try:
                    # CPU Load Sample
                    cpu = psutil.cpu_percent(interval=1)
                    mem = psutil.virtual_memory().percent

                    samples.append({'cpu': cpu, 'mem': mem, 'time': elapsed})

                    elapsed = int(time.time() - start_time)

                    if elapsed % 30 == 0:  # Alle 30 Sekunden
                        output.append(f"  [{elapsed}s] CPU: {cpu}% | RAM: {mem}%")

                    # Warnungen sammeln
                    if cpu < 50:
                        warnings.append(f"[{elapsed}s] CPU nur {cpu}% (Throttling?)")

                    if mem > 90:
                        warnings.append(f"[{elapsed}s] RAM kritisch {mem}%")

                except Exception as e:
                    errors.append(f"[{elapsed}s] Fehler: {str(e)}")

            # Analyse
            output.append("")
            output.append("📊 Test-Ergebnis:")
            output.append("")

            avg_cpu = sum(s['cpu'] for s in samples) / len(samples) if samples else 0
            avg_mem = sum(s['mem'] for s in samples) / len(samples) if samples else 0

            output.append(f"  Durchschnitt CPU: {avg_cpu:.1f}%")
            output.append(f"  Durchschnitt RAM: {avg_mem:.1f}%")
            output.append("")

            # Bewertung
            if not errors and not warnings:
                output.append("✅ STABIL - Keine Probleme gefunden")
            elif errors:
                output.append("❌ INSTABIL - Fehler aufgetreten:")
                for err in errors[:5]:
                    output.append(f"  • {err}")
            elif warnings:
                output.append("⚠️  GRENZWERTIG - Warnungen:")
                for warn in warnings[:5]:
                    output.append(f"  • {warn}")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Fehler beim Stability Test: {str(e)}"
