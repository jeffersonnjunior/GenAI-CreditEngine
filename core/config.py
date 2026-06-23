from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    name: str = "creditengine"

    @property
    def url(self) -> str:
        password = self.password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.user}:{password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr | None = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    mock: bool = False
    max_healing_attempts: int = 3

    @property
    def use_mock(self) -> bool:
        return self.mock or self.api_key is None


class ChromaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHROMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    persist_dir: Path = PROJECT_ROOT / ".chroma"
    collection_name: str = "compliance_rules"
    sentence_window_size: int = 2
    rrf_k: int = 60
    top_k: int = 5


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GenAI CreditEngine"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    compliance_manual_path: Path = PROJECT_ROOT / "data" / "compliance_manual.md"
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
