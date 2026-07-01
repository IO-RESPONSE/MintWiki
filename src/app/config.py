from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="wiki-engine")
    environment: str = Field(default="development")
    database_url: str = Field(default="postgresql://localhost/wiki_engine")
    redis_url: str = Field(default="redis://localhost:6379/0")

    model_config = SettingsConfigDict(env_prefix="WIKI_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()

