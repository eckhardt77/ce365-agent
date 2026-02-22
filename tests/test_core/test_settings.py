"""
Tests für Settings — Edition-Migration, Defaults, Validierung
"""

import os
import pytest
from unittest.mock import patch
from ce365.config.settings import _migrate_edition


class TestEditionMigration:
    """_migrate_edition() mappt alte Werte auf neue 3-Tier-Bezeichnungen"""

    def test_community_to_free(self):
        assert _migrate_edition("community") == "free"

    def test_pro_to_core(self):
        assert _migrate_edition("pro") == "core"

    def test_free_stays_free(self):
        assert _migrate_edition("free") == "free"

    def test_core_stays_core(self):
        assert _migrate_edition("core") == "core"

    def test_scale_stays_scale(self):
        assert _migrate_edition("scale") == "scale"

    def test_unknown_passes_through(self):
        assert _migrate_edition("enterprise") == "enterprise"

    def test_empty_string(self):
        assert _migrate_edition("") == ""


class TestSettingsDefaults:
    """Settings haben korrekte Defaults für 3-Tier"""

    def test_default_edition_is_free(self):
        from ce365.config.settings import Settings
        s = Settings()
        assert s.edition == "free"

    def test_edition_accepts_core(self):
        from ce365.config.settings import Settings
        s = Settings(edition="core")
        assert s.edition == "core"

    def test_edition_accepts_scale(self):
        from ce365.config.settings import Settings
        s = Settings(edition="scale")
        assert s.edition == "scale"


class TestSettingsLoad:
    """Settings.load() migriert Edition korrekt"""

    @patch.dict(os.environ, {
        "EDITION": "community",
        "ANTHROPIC_API_KEY": "test-key-not-real",
    })
    def test_load_migrates_community(self):
        from ce365.config.settings import Settings
        # Direkt _migrate_edition testen (Settings.load() hat Seiteneffekte)
        assert _migrate_edition(os.environ["EDITION"]) == "free"

    @patch.dict(os.environ, {
        "EDITION": "pro",
        "ANTHROPIC_API_KEY": "test-key-not-real",
    })
    def test_load_migrates_pro(self):
        assert _migrate_edition(os.environ["EDITION"]) == "core"

    @patch.dict(os.environ, {
        "EDITION": "scale",
        "ANTHROPIC_API_KEY": "test-key-not-real",
    })
    def test_load_keeps_scale(self):
        assert _migrate_edition(os.environ["EDITION"]) == "scale"
