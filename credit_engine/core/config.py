from enum import StrEnum

from pydantic import AliasChoices, Field
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
    """LLM backend for self-healing (stub in tests; Gemini/Ollama in local/dev)."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    BACKEND: str = "stub"
    """Active healer: stub | gemini | openai_compatible | llama."""
    MODEL: str = "gemini-2.0-flash"
    """Model id (Gemini id, or Ollama/vLLM served name)."""
    API_KEY: str = ""
    """API key when required (Gemini; optional for local Ollama)."""
    # Distinct names so Settings does not clash with BureauSettings.BASE_URL.
    OPENAI_BASE_URL: str = Field(
        default="http://127.0.0.1:11434/v1",
        validation_alias=AliasChoices("OPENAI_BASE_URL", "BASE_URL"),
    )
    """OpenAI-compatible base URL (env: LLM_BASE_URL or LLM_OPENAI_BASE_URL)."""
    OPENAI_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        validation_alias=AliasChoices("OPENAI_TIMEOUT_SECONDS", "TIMEOUT_SECONDS"),
    )
    """HTTP timeout for openai_compatible / llama healers."""


class BureauSettings(BaseSettings):
    """Credit bureau client selection."""

    model_config = SettingsConfigDict(env_prefix="BUREAU_")

    CLIENT: str = "stub"
    """Bureau backend: stub | unavailable | http."""
    STUB_DEFAULT_SCORE: int = 650
    """Score returned by the stub bureau for any CPF."""
    BASE_URL: str = ""
    """Base URL for BUREAU_CLIENT=http (e.g. http://localhost:9090)."""
    TIMEOUT_SECONDS: float = 3.0
    """HTTP timeout before degrading to the emergency limit."""


class DatabaseSettings(BaseSettings):
    """Async SQLAlchemy database settings."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    URL: str = "sqlite+aiosqlite:///./data/credit_engine.db"
    """SQLAlchemy async URL (SQLite by default)."""


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
    SENTENCE_WINDOW: bool = True
    """Index sentence windows and expand to parent sections on retrieve."""
    WINDOW_SENTENCES: int = 2
    """How many sentences per indexed window."""
    WINDOW_OVERLAP: int = 0
    """Overlap in sentences between consecutive windows."""
    RRF_ENABLED: bool = True
    """Fuse vector and lexical rankings with Reciprocal Rank Fusion."""
    RRF_K: int = 60
    """RRF constant (classic default is 60)."""
    RRF_CANDIDATES: int = 8
    """How many vector hits to consider before RRF / expansion."""


class EnvSettings(BaseSettings):
    """Environment settings."""

    ENV: EnvEnum = EnvEnum.LOCAL


class AgentSettings(BaseSettings):
    """Proposal orchestration backend."""

    model_config = SettingsConfigDict(env_prefix="AGENT_")

    ORCHESTRATOR: str = "graph"
    """Orchestrator: graph (LangGraph) | linear (legacy sequential)."""


class Settings(
    AppSettings,
    UvicornSettings,
    CORSSettings,
    CreditSettings,
    HealingSettings,
    LlmSettings,
    BureauSettings,
    DatabaseSettings,
    RagSettings,
    AgentSettings,
    EnvSettings,
):
    """Aggregated settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
