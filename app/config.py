from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    targets_path: str = "targets.yaml"
    log_level: str = "info"


settings = Settings()
