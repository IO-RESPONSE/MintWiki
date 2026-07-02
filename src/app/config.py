from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="wiki-engine")
    environment: str = Field(default="development")
    database_url: str = Field(default="postgresql://localhost/wiki_engine")
    redis_url: str = Field(default="redis://localhost:6379/0")
    # MariaDB DSN placeholder (docs/ansi-sql-persistence-policy.md 0470 항목).
    # 현재는 값을 읽어 두기만 하며, database.py는 아직 이 값을 쓰지 않는다.
    # 실제 드라이버 전환/이중화는 0470 이후 잡의 범위다.
    mariadb_dsn: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(env_prefix="WIKI_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()

