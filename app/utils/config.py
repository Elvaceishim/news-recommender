from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

settings = Settings()
