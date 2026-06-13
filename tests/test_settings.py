from trading_assistant.settings import Settings


def test_default_settings_use_local_values():
    settings = Settings()

    assert settings.app_name == "a-share-short-term-trading-assistant"
    assert settings.environment == "local"
    assert settings.database_url.startswith("sqlite")
    assert settings.redis_url == "redis://localhost:6379/0"
