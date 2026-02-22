"""
Tests für LicenseValidator + Edition Features (3-Tier: free/core/scale)
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from ce365.core.license import LicenseValidator, check_edition_features


@pytest.fixture
def license_validator(tmp_ce365_dir):
    """LicenseValidator mit temporärem Cache"""
    return LicenseValidator(
        license_server_url="http://test-server:9000",
        cache_dir=tmp_ce365_dir / "cache"
    )


class TestHMACCache:
    """Tests für HMAC-gesicherten License Cache"""

    def test_cache_and_load(self, license_validator):
        result = {
            "valid": True,
            "edition": "core",
            "expires_at": "never",
            "customer_name": "Test Corp"
        }
        license_validator._cache_license("TEST-KEY-123", result)

        loaded = license_validator._load_cached_license("TEST-KEY-123")
        assert loaded is not None
        assert loaded["valid"] is True
        assert loaded["edition"] == "core"

    def test_wrong_key_returns_none(self, license_validator):
        result = {"valid": True, "edition": "core"}
        license_validator._cache_license("KEY-1", result)
        assert license_validator._load_cached_license("KEY-2") is None

    def test_tampered_cache_returns_none(self, license_validator):
        result = {"valid": True, "edition": "core"}
        license_validator._cache_license("TEST-KEY", result)

        cache_data = json.loads(license_validator.cache_file.read_text())
        cache_data["signature"] = "tampered_signature"
        license_validator.cache_file.write_text(json.dumps(cache_data))

        assert license_validator._load_cached_license("TEST-KEY") is None

    def test_expired_cache_returns_none(self, license_validator):
        result = {"valid": True, "edition": "core"}
        license_validator._cache_license("TEST-KEY", result)

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
        result = {"valid": True, "edition": "core", "expires_at": yesterday}
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
            "edition": "core",
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
        assert result["edition"] == "core"

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

        cached_result = {"valid": True, "edition": "core", "expires_at": "never"}
        license_validator._cache_license("TEST-KEY", cached_result)

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


# ==========================================================
# Edition Features — 3-Tier Hierarchie (free < core < scale)
# ==========================================================

class TestFreeFeatures:
    """Free hat nur Basis-Features"""

    def test_free_has_local_learning(self):
        assert check_edition_features("free", "local_learning") is True

    def test_free_has_pii_detection(self):
        assert check_edition_features("free", "pii_detection") is True

    def test_free_no_unlimited_repairs(self):
        assert check_edition_features("free", "unlimited_repairs") is False

    def test_free_no_advanced_audit(self):
        assert check_edition_features("free", "advanced_audit") is False

    def test_free_no_advanced_repair(self):
        assert check_edition_features("free", "advanced_repair") is False

    def test_free_no_web_search(self):
        assert check_edition_features("free", "web_search") is False

    def test_free_no_ssh_remote(self):
        assert check_edition_features("free", "ssh_remote") is False

    def test_free_no_hooks(self):
        assert check_edition_features("free", "hooks") is False

    def test_free_no_pdf_report(self):
        assert check_edition_features("free", "pdf_report") is False

    def test_free_no_commercial_use(self):
        assert check_edition_features("free", "commercial_use") is False

    def test_free_no_shared_learning(self):
        assert check_edition_features("free", "shared_learning") is False

    def test_free_no_mcp(self):
        assert check_edition_features("free", "mcp_integration") is False


class TestCoreFeatures:
    """Core hat Free + eigene Features, aber kein Scale"""

    def test_core_inherits_free(self):
        assert check_edition_features("core", "local_learning") is True
        assert check_edition_features("core", "pii_detection") is True

    def test_core_has_unlimited_repairs(self):
        assert check_edition_features("core", "unlimited_repairs") is True

    def test_core_has_advanced_audit(self):
        assert check_edition_features("core", "advanced_audit") is True

    def test_core_has_advanced_repair(self):
        assert check_edition_features("core", "advanced_repair") is True

    def test_core_has_web_search(self):
        assert check_edition_features("core", "web_search") is True

    def test_core_has_ssh_remote(self):
        assert check_edition_features("core", "ssh_remote") is True

    def test_core_has_hooks(self):
        assert check_edition_features("core", "hooks") is True

    def test_core_has_pdf_report(self):
        assert check_edition_features("core", "pdf_report") is True

    def test_core_has_commercial_use(self):
        assert check_edition_features("core", "commercial_use") is True

    def test_core_has_system_control(self):
        assert check_edition_features("core", "system_control") is True

    def test_core_no_shared_learning(self):
        assert check_edition_features("core", "shared_learning") is False

    def test_core_no_mcp(self):
        assert check_edition_features("core", "mcp_integration") is False

    def test_core_no_shared_playbooks(self):
        assert check_edition_features("core", "shared_playbooks") is False


class TestScaleFeatures:
    """Scale hat alles aus Core + eigene Features"""

    def test_scale_inherits_free(self):
        assert check_edition_features("scale", "local_learning") is True
        assert check_edition_features("scale", "pii_detection") is True

    def test_scale_inherits_core(self):
        assert check_edition_features("scale", "unlimited_repairs") is True
        assert check_edition_features("scale", "advanced_audit") is True
        assert check_edition_features("scale", "ssh_remote") is True
        assert check_edition_features("scale", "hooks") is True
        assert check_edition_features("scale", "pdf_report") is True
        assert check_edition_features("scale", "commercial_use") is True

    def test_scale_has_shared_learning(self):
        assert check_edition_features("scale", "shared_learning") is True

    def test_scale_has_mcp(self):
        assert check_edition_features("scale", "mcp_integration") is True

    def test_scale_has_shared_playbooks(self):
        assert check_edition_features("scale", "shared_playbooks") is True

    def test_scale_has_api_access(self):
        assert check_edition_features("scale", "api_access") is True

    def test_scale_has_analytics(self):
        assert check_edition_features("scale", "analytics_extended") is True


class TestEdgesCases:
    """Unbekannte Editionen und Features"""

    def test_unknown_edition_gets_free_fallback(self):
        """Unbekannte Editionen bekommen Free-Features als Fallback"""
        assert check_edition_features("unknown", "local_learning") is True
        assert check_edition_features("unknown", "unlimited_repairs") is False

    def test_unknown_feature_returns_false(self):
        assert check_edition_features("scale", "nonexistent_feature") is False

    def test_empty_edition_gets_free_fallback(self):
        """Leere Edition bekommt Free-Features als Fallback"""
        assert check_edition_features("", "local_learning") is True
        assert check_edition_features("", "ssh_remote") is False

    def test_old_community_gets_free_fallback(self):
        """Alte 'community' Edition bekommt Free-Fallback"""
        assert check_edition_features("community", "local_learning") is True
        assert check_edition_features("community", "unlimited_repairs") is False

    def test_old_pro_gets_free_fallback(self):
        """Alte 'pro' Edition bekommt Free-Fallback (nicht Core!)"""
        assert check_edition_features("pro", "local_learning") is True
        assert check_edition_features("pro", "unlimited_repairs") is False
