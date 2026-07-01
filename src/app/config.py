from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="wiki-engine")
    environment: str = Field(default="development")

    model_config = SettingsConfigDict(env_prefix="WIKI_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()

