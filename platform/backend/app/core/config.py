from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UTN International Research Collaboration API"
    environment: str = "development"
    secret_key: str = "development-only-change-me"
    access_token_minutes: int = 480
    database_url: str = "sqlite:///./utn.db"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: str = "http://localhost:3000"
    scopus_mode: str = "mock"
    elsevier_api_key: str = ""
    elsevier_inst_token: str = ""
    elsevier_base_url: str = "https://api.elsevier.com/content"
    scopus_request_timeout: float = 30
    scopus_max_retries: int = 3
    max_csv_bytes: int = 10_000_000
    export_dir: str = "./exports"
    scheduled_sync_secret: str = ""
    initial_admin_name: str = ""
    initial_admin_email: str = ""
    initial_admin_password: str = ""
    utn_aliases: str = "University of Technology Nuremberg|Technische Universität Nürnberg|UTN"
    utn_affiliation_ids: str = ""
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
