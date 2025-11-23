from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_PATH = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    """Configuration for Spoon analysis worker."""

    model_config = SettingsConfigDict(
        env_file=_ENV_PATH if _ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
    )

    # NATS Configuration
    nats_url: str = Field("nats://localhost:4222", alias="NATS_URL")
    spoon_analysis_subject: str = Field("spoon.analysis", alias="SPOON_ANALYSIS_SUBJECT")
    insight_result_subject: str = Field("insight.results", alias="INSIGHT_RESULT_SUBJECT")

    # Logging
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        "INFO", alias="LOG_LEVEL"
    )

    # OpenAI Configuration (optimized for detailed crypto analysis)
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: str = Field("https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_temperature: float = Field(0.2, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(2000, alias="SPOON_OPENAI_MAX_TOKENS")  # Separate from insight_worker

    # External APIs
    tavily_api_key: Optional[str] = Field(None, alias="TAVILY_API_KEY")

    # Analysis Configuration
    report_timezone: str = Field("UTC", alias="REPORT_TIMEZONE")
    default_popular_coins: list[str] = Field(
        default=["BTC", "ETH", "SOL", "BNB", "XRP"],
        alias="DEFAULT_POPULAR_COINS"
    )

    @property
    def env_file(self) -> Optional[Path]:
        return _ENV_PATH if _ENV_PATH.exists() else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
