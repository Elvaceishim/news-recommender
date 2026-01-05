from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    LOG_LEVEL: str = "INFO"

    # HuggingFace API token (for embeddings - get from huggingface.co/settings/tokens)
    HF_API_TOKEN: str | None = None

    # Cron ingestion secret (for external cron services)
    CRON_SECRET: str | None = None

    # JWT Config
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()
