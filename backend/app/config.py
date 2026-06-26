"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # M1 Mode: skip DB/Redis/OpenAI, use in-memory Solver + AI fallback
    fake_mode: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://poker:poker_dev@localhost:5432/pokercoachai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Solver
    solver_provider: str = "texas"
    solver_timeout_seconds: int = 10

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
