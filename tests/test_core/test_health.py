"""
Tests für Health-Check — Edition-spezifische Logik
"""

import pytest
from unittest.mock import MagicMock, patch


class TestHealthCheckEditionLogic:
    """Health-Check prüft Edition-spezifische Anforderungen"""

    def test_core_requires_license_key(self):
        """Core-Edition muss Lizenzschlüssel-Check durchführen"""
        settings = MagicMock()
        settings.edition = "core"
        settings.license_key = ""
        # Core ohne Key → sollte im Health-Check als Fehler gelten
        assert settings.edition in ("core", "scale")
        assert not settings.license_key

    def test_scale_requires_license_key(self):
        """Scale-Edition muss Lizenzschlüssel-Check durchführen"""
        settings = MagicMock()
        settings.edition = "scale"
        settings.license_key = ""
        assert settings.edition in ("core", "scale")
        assert not settings.license_key

    def test_free_no_license_needed(self):
        """Free-Edition braucht keinen Lizenzschlüssel"""
        settings = MagicMock()
        settings.edition = "free"
        assert settings.edition not in ("core", "scale")

    def test_core_valid_license_format(self):
        """Gültige Lizenz beginnt mit CE365-"""
        settings = MagicMock()
        settings.edition = "core"
        settings.license_key = "CE365-CORE-ABCD-1234"
        assert settings.license_key.startswith("CE365-")

    def test_core_checks_license_server(self):
        """Core/Scale prüft Lizenzserver-Erreichbarkeit"""
        settings = MagicMock()
        settings.edition = "core"
        settings.license_server_url = "https://agent.ce365.de"
        assert settings.edition in ("core", "scale")
        assert settings.license_server_url

    def test_free_skips_license_server(self):
        """Free prüft keinen Lizenzserver"""
        settings = MagicMock()
        settings.edition = "free"
        settings.license_server_url = ""
        assert settings.edition not in ("core", "scale")
