from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvEnum(StrEnum):
    """Defines the project environment."""

    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


class LogLevel(StrEnum):
    """Define possible log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AppSettings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_prefix="APP_")

    NAME: str = "GenAI-CreditEngine"
    DESCRIPTION: str = "Plataforma multiagente de concessão de crédito"
    VERSION: str = "0.1.0"


class UvicornSettings(BaseSettings):
    """Uvicorn settings."""

    WORKERS_COUNT: int = 1
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8080
    RELOAD: bool = True
    LOG_LEVEL: LogLevel = LogLevel.INFO


class CORSSettings(BaseSettings):
    """CORS settings."""

    CORS_ALLOW_ORIGINS: list[str] = Field(default=["*"])
    CORS_ALLOW_METHODS: list[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"])
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_EXPOSE_HEADERS: list[str] | str = Field(default=["*"])
    CORS_MAX_AGE: int = 600


class CreditSettings(BaseSettings):
    """Credit risk thresholds (deterministic rules)."""

    model_config = SettingsConfigDict(env_prefix="CREDIT_")

    MIN_SCORE_TO_APPROVE: int = 300
    """Scores below this value get limit R$ 0."""
    INCOME_LIMIT_RATIO: float = 0.10
    """Limit ratio for scores in [MIN_SCORE_TO_APPROVE, HIGH_SCORE_THRESHOLD)."""
    HIGH_SCORE_THRESHOLD: int = 700
    """Scores at or above this value use HIGH_INCOME_LIMIT_RATIO."""
    HIGH_INCOME_LIMIT_RATIO: float = 0.30
    """Approved limit ratio for high-score applicants."""
    EMERGENCY_LIMIT: float = 500.0
    """Fixed limit when the credit bureau is unavailable (contingency rule)."""
    AUTONOMOUS_LIMIT_CAP: float = 10000.0
    """Above this calculated limit, approval requires human override (HITL)."""


class HealingSettings(BaseSettings):
    """Self-healing ingest settings."""

    model_config = SettingsConfigDict(env_prefix="HEALING_")

    MAX_ATTEMPTS: int = 3
    """How many times the healer may rewrite an invalid payload."""


class LlmSettings(BaseSettings):
    """LLM backend for self-healing (stub in tests; Gemini in local/dev)."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    BACKEND: str = "stub"
    """Active healer: stub | gemini."""
    MODEL: str = "gemini-2.0-flash"
    """Gemini model id when BACKEND=gemini."""
    API_KEY: str = ""
    """Google AI Studio / Gemini API key (required for BACKEND=gemini)."""


class BureauSettings(BaseSettings):
    """Credit bureau client selection — real HTTP client is pending."""

    model_config = SettingsConfigDict(env_prefix="BUREAU_")

    CLIENT: str = "stub"
    """Use stub until Serasa/Boa Vista integration exists (stub | unavailable)."""
    STUB_DEFAULT_SCORE: int = 650
    """Score returned by the stub bureau for any CPF."""


class RagSettings(BaseSettings):
    """Compliance RAG (Chroma) settings."""

    model_config = SettingsConfigDict(env_prefix="RAG_")

    ENABLED: bool = True
    """When false, decisions skip policy retrieval."""
    PERSIST_DIR: str = ".chroma"
    """Chroma persistence directory (empty / unused in ephemeral test stores)."""
    COLLECTION_NAME: str = "compliance"
    """Chroma collection name for policy chunks."""
    TOP_K: int = 2
    """How many policy excerpts to attach to each decision."""
    POLICY_PATH: str = ""
    """Optional override path to the markdown policy; empty uses package default."""


class EnvSettings(BaseSettings):
    """Environment settings."""

    ENV: EnvEnum = EnvEnum.LOCAL


class Settings(
    AppSettings,
    UvicornSettings,
    CORSSettings,
    CreditSettings,
    HealingSettings,
    LlmSettings,
    BureauSettings,
    RagSettings,
    EnvSettings,
):
    """Aggregated settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
