from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str  # No default — must be set via .env or environment
    secret_key: str  # No default — must be set via .env or environment
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    sql_echo: bool = False
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
