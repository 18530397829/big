from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "a-share-short-term-trading-assistant"
    environment: str = "local"
    database_url: str = "sqlite:///./trading_assistant.db"
    redis_url: str = "redis://localhost:6379/0"
    tushare_token: str = ""
    openai_api_key: str = ""
    feishu_webhook_url: str = ""
