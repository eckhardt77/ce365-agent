"""
Tests für System Fingerprinting

Testet Fingerprint-Generierung, Caching und Stabilität.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from techcare.core.system_fingerprint import (
    get_system_fingerprint,
    get_cached_fingerprint,
    save_fingerprint,
    get_or_create_fingerprint,
)


class TestFingerprintGeneration:
    """Tests für Fingerprint-Generierung"""

    def test_returns_hex_string(self):
        fp = get_system_fingerprint()
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA256 hex length
        # Validate hex characters
        int(fp, 16)

    def test_deterministic(self):
        fp1 = get_system_fingerprint()
        fp2 = get_system_fingerprint()
        assert fp1 == fp2

    def test_not_empty(self):
        fp = get_system_fingerprint()
        assert fp != ""
        assert fp != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # SHA256 of empty string


class TestFingerprintCache:
    """Tests für Fingerprint Caching"""

    def test_save_and_load(self, tmp_path):
        cache_file = tmp_path / ".techcare" / "fingerprint"
        with patch("techcare.core.system_fingerprint.Path.home", return_value=tmp_path):
            save_fingerprint("test-fingerprint-123")
            result = get_cached_fingerprint()
            assert result == "test-fingerprint-123"

    def test_no_cache_returns_none(self, tmp_path):
        with patch("techcare.core.system_fingerprint.Path.home", return_value=tmp_path):
            result = get_cached_fingerprint()
            assert result is None


class TestGetOrCreateFingerprint:
    """Tests für get_or_create_fingerprint()"""

    def test_creates_fingerprint_when_no_cache(self, tmp_path):
        with patch("techcare.core.system_fingerprint.Path.home", return_value=tmp_path):
            fp = get_or_create_fingerprint()
            assert isinstance(fp, str)
            assert len(fp) == 64

    def test_returns_cached_when_available(self, tmp_path):
        cache_dir = tmp_path / ".techcare"
        cache_dir.mkdir(parents=True)
        (cache_dir / "fingerprint").write_text("cached-fp-abc")

        with patch("techcare.core.system_fingerprint.Path.home", return_value=tmp_path):
            fp = get_or_create_fingerprint()
            assert fp == "cached-fp-abc"

    def test_caches_after_creation(self, tmp_path):
        with patch("techcare.core.system_fingerprint.Path.home", return_value=tmp_path):
            fp = get_or_create_fingerprint()
            cache_file = tmp_path / ".techcare" / "fingerprint"
            assert cache_file.exists()
            assert cache_file.read_text() == fp
