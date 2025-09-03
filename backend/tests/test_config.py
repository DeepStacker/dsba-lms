import pytest
from app.core.config import Settings, settings


class TestSettings:
    """Test cases for application configuration."""

    def test_settings_defaults(self):
        """Test that settings have proper default values."""
        test_settings = Settings()

        assert test_settings.postgres_host == "localhost"
        assert test_settings.postgres_db == "apollo"
        assert test_settings.postgres_user == "apollo"
        assert test_settings.postgres_password == "apollo"
        assert test_settings.environment == "development"
        assert test_settings.jwt_expires_min == 15
        assert test_settings.refresh_expires_days == 7

    def test_settings_property_sync_database_url(self):
        """Test that sync_database_url property works correctly."""
        test_settings = Settings()
        expected_url = "postgresql://apollo:apollo@localhost/apollo"
        assert test_settings.sync_database_url == expected_url

    def test_settings_property_async_database_url(self):
        """Test that async_database_url property works correctly."""
        test_settings = Settings()
        expected_url = "postgresql+asyncpg://apollo:apollo@localhost/apollo"
        assert test_settings.async_database_url == expected_url

    def test_settings_custom_database_url(self):
        """Test that custom database URL is used when provided."""
        custom_url = "postgresql://user:pass@host:5432/db"
        test_settings = Settings(database_url=custom_url)
        assert test_settings.sync_database_url == custom_url

    def test_settings_features(self):
        """Test feature flags have correct defaults."""
        test_settings = Settings()
        assert test_settings.feature_ai is True
        assert test_settings.feature_telemetry is True


class TestGlobalSettings:
    """Test the global settings instance."""

    def test_global_settings_instance(self):
        """Test that global settings instance exists and has expected attributes."""
        assert hasattr(settings, 'postgres_host')
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'sync_database_url')
        assert hasattr(settings, 'async_database_url')
