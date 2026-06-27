"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # M1 Mode: skip DB/Redis/AI, use in-memory Solver + AI fallback
    fake_mode: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://poker:poker_dev@localhost:5432/pokercoachai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI Provider
    ai_provider: str = "deepseek"  # "deepseek" | "openai"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-pro"
    deepseek_reasoning_effort: str = "medium"  # "low" | "medium" | "high"
    deepseek_thinking: str = "enabled"          # "enabled" | "disabled"

    # OpenAI (legacy)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Solver
    solver_provider: str = "texas"
    solver_timeout_seconds: int = 10

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
