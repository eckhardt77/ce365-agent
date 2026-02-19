#!/usr/bin/env python3
"""
CE365 Agent - Build Release Script

Builds a standalone Pro binary using PyInstaller.
Output: dist/ce365-pro-{version}-{platform}.{ext}

Usage:
    python scripts/build_release.py
"""

import os
import sys
import platform
import hashlib
import subprocess
from pathlib import Path

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ce365.__version__ import __version__


def get_platform_info():
    """Plattform und Architektur ermitteln"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        arch = "arm64" if machine == "arm64" else "amd64"
        return f"macos-{arch}", ""
    elif system == "windows":
        arch = "amd64" if machine in ("amd64", "x86_64") else machine
        return f"win-{arch}", ".exe"
    else:
        arch = "amd64" if machine in ("x86_64", "amd64") else machine
        return f"linux-{arch}", ""


def sha256_file(filepath):
    """SHA256 Checksumme berechnen"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build():
    """PyInstaller Build ausführen"""
    plat, ext = get_platform_info()
    output_name = f"ce365-pro-{__version__}-{plat}"
    dist_dir = PROJECT_ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)

    print(f"Building CE365 Pro v{__version__} for {plat}...")
    print(f"Output: dist/{output_name}{ext}")
    print()

    # PyInstaller Kommando
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", output_name,
        "--distpath", str(dist_dir),
        "--workpath", str(PROJECT_ROOT / "build"),
        "--specpath", str(PROJECT_ROOT / "build"),
        # Hidden imports die PyInstaller nicht automatisch findet
        "--hidden-import", "anthropic",
        "--hidden-import", "openai",
        "--hidden-import", "httpx",
        "--hidden-import", "rich",
        "--hidden-import", "pydantic",
        "--hidden-import", "dotenv",
        "--hidden-import", "bcrypt",
        "--hidden-import", "psutil",
        "--hidden-import", "ce365",
        "--hidden-import", "ce365.core",
        "--hidden-import", "ce365.core.bot",
        "--hidden-import", "ce365.core.agents",
        "--hidden-import", "ce365.core.providers",
        "--hidden-import", "ce365.tools",
        "--hidden-import", "ce365.config",
        "--hidden-import", "ce365.ui",
        "--hidden-import", "ce365.learning",
        "--hidden-import", "ce365.workflow",
        "--hidden-import", "ce365.security",
        "--hidden-import", "ce365.setup",
        "--hidden-import", "ce365.i18n",
        # Daten-Dateien
        "--add-data", f"ce365/i18n:ce365/i18n",
        "--add-data", f"ce365/tools/drivers:ce365/tools/drivers",
        "--add-data", f"DISCLAIMER.txt:.",
        # Clean build
        "--clean",
        "--noconfirm",
        # Entry point
        str(PROJECT_ROOT / "ce365" / "__main__.py"),
    ]

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(1)

    # Output prüfen
    output_file = dist_dir / f"{output_name}{ext}"
    if not output_file.exists():
        print(f"Error: {output_file} not found after build")
        sys.exit(1)

    # Checksumme
    checksum = sha256_file(output_file)
    size_mb = output_file.stat().st_size / (1024 * 1024)

    checksums_file = dist_dir / "checksums.txt"
    with open(checksums_file, "a") as f:
        f.write(f"{checksum}  {output_name}{ext}\n")

    print()
    print(f"Build successful!")
    print(f"  File: dist/{output_name}{ext}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  SHA256: {checksum}")
    print(f"  Checksums: dist/checksums.txt")


if __name__ == "__main__":
    build()
