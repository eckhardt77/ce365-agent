"""
Tests für LicenseValidator

Testet HMAC Cache, Online/Offline Validation und Edition Features.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from techcare.core.license import LicenseValidator, check_edition_features


@pytest.fixture
def license_validator(tmp_techcare_dir):
    """LicenseValidator mit temporärem Cache"""
    return LicenseValidator(
        backend_url="http://test-backend:8000",
        cache_dir=tmp_techcare_dir / "cache"
    )


class TestHMACCache:
    """Tests für HMAC-gesicherten License Cache"""

    def test_cache_and_load(self, license_validator):
        result = {
            "valid": True,
            "edition": "pro",
            "expires_at": "never",
            "customer_name": "Test Corp"
        }
        license_validator._cache_license("TEST-KEY-123", result)

        loaded = license_validator._load_cached_license("TEST-KEY-123")
        assert loaded is not None
        assert loaded["valid"] is True
        assert loaded["edition"] == "pro"

    def test_wrong_key_returns_none(self, license_validator):
        result = {"valid": True, "edition": "pro"}
        license_validator._cache_license("KEY-1", result)
        assert license_validator._load_cached_license("KEY-2") is None

    def test_tampered_cache_returns_none(self, license_validator):
        result = {"valid": True, "edition": "pro"}
        license_validator._cache_license("TEST-KEY", result)

        # Manipulate cache file
        cache_data = json.loads(license_validator.cache_file.read_text())
        cache_data["signature"] = "tampered_signature"
        license_validator.cache_file.write_text(json.dumps(cache_data))

        assert license_validator._load_cached_license("TEST-KEY") is None

    def test_expired_cache_returns_none(self, license_validator):
        result = {"valid": True, "edition": "pro"}
        license_validator._cache_license("TEST-KEY", result)

        # Set cache timestamp to 25 hours ago
        signed_data = json.loads(license_validator.cache_file.read_text())
        payload = json.loads(signed_data["payload"])
        payload["cached_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
        new_payload = json.dumps(payload, sort_keys=True)
        signed_data["payload"] = new_payload
        signed_data["signature"] = license_validator._compute_hmac(new_payload)
        license_validator.cache_file.write_text(json.dumps(signed_data))

        assert license_validator._load_cached_license("TEST-KEY") is None

    def test_expired_license_returns_invalid(self, license_validator):
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        result = {"valid": True, "edition": "pro", "expires_at": yesterday}
        license_validator._cache_license("TEST-KEY", result)

        loaded = license_validator._load_cached_license("TEST-KEY")
        assert loaded is not None
        assert loaded["valid"] is False
        assert "abgelaufen" in loaded.get("error", "")

    def test_no_cache_file_returns_none(self, license_validator):
        assert license_validator._load_cached_license("TEST-KEY") is None


class TestOnlineValidation:
    """Tests für Online-Validierung"""

    @pytest.mark.asyncio
    async def test_successful_online_validation(self, license_validator):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "edition": "pro",
            "expires_at": "never",
            "customer_name": "Test"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await license_validator.validate("TEST-KEY", "fingerprint-123")

        assert result["valid"] is True
        assert result["edition"] == "pro"

    @pytest.mark.asyncio
    async def test_server_error(self, license_validator):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await license_validator.validate("TEST-KEY")

        assert result["valid"] is False
        assert "500" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_offline_fallback(self, license_validator):
        import httpx

        # Pre-cache a valid license
        cached_result = {"valid": True, "edition": "pro", "expires_at": "never"}
        license_validator._cache_license("TEST-KEY", cached_result)

        # Simulate connection error
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("No connection")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await license_validator.validate("TEST-KEY")

        assert result["valid"] is True
        assert result.get("_offline") is True

    @pytest.mark.asyncio
    async def test_offline_no_cache(self, license_validator):
        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("No connection")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = await license_validator.validate("TEST-KEY")

        assert result["valid"] is False
        assert "nicht erreichbar" in result.get("error", "")


class TestEditionFeatures:
    """Tests für Edition Feature Checks (Free / Pro / Business)"""

    def test_free_has_basic_features(self):
        assert check_edition_features("free", "local_learning") is True
        assert check_edition_features("free", "pii_detection") is True
        assert check_edition_features("free", "unlimited_repairs") is False
        assert check_edition_features("free", "advanced_audit") is False
        assert check_edition_features("free", "advanced_repair") is False
        assert check_edition_features("free", "web_search") is False
        assert check_edition_features("free", "root_cause_analysis") is False
        assert check_edition_features("free", "monitoring") is False
        assert check_edition_features("free", "shared_learning") is False

    def test_pro_features(self):
        assert check_edition_features("pro", "local_learning") is True
        assert check_edition_features("pro", "pii_detection") is True
        assert check_edition_features("pro", "unlimited_repairs") is True
        assert check_edition_features("pro", "advanced_audit") is True
        assert check_edition_features("pro", "advanced_repair") is True
        assert check_edition_features("pro", "web_search") is True
        assert check_edition_features("pro", "root_cause_analysis") is True
        assert check_edition_features("pro", "system_report") is True
        assert check_edition_features("pro", "driver_management") is True
        assert check_edition_features("pro", "unlimited_systems") is False
        assert check_edition_features("pro", "monitoring") is False
        assert check_edition_features("pro", "shared_learning") is False

    def test_business_all_features(self):
        assert check_edition_features("business", "local_learning") is True
        assert check_edition_features("business", "pii_detection") is True
        assert check_edition_features("business", "unlimited_repairs") is True
        assert check_edition_features("business", "advanced_audit") is True
        assert check_edition_features("business", "advanced_repair") is True
        assert check_edition_features("business", "web_search") is True
        assert check_edition_features("business", "root_cause_analysis") is True
        assert check_edition_features("business", "system_report") is True
        assert check_edition_features("business", "driver_management") is True
        assert check_edition_features("business", "unlimited_systems") is True
        assert check_edition_features("business", "monitoring") is True
        assert check_edition_features("business", "shared_learning") is True
        assert check_edition_features("business", "team_features") is True

    def test_unknown_edition(self):
        assert check_edition_features("unknown", "monitoring") is False

    def test_unknown_feature(self):
        assert check_edition_features("business", "nonexistent_feature") is False
