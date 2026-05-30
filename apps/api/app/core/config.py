from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(raw: str) -> str:
    """Asegura que SQLAlchemy use el driver psycopg v3.

    Fly Managed Postgres entrega URLs con esquema 'postgres://' o
    'postgresql://'. SQLAlchemy por default intenta psycopg2 con esos
    esquemas; nuestra imagen sólo trae psycopg v3.
    """
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


class Settings(BaseSettings):
    api_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    # Auth simple por API key compartida (header X-API-Key). Si queda vacía,
    # la autenticación está DESACTIVADA (compatibilidad con el MVP actual).
    # En prod: `fly secrets set API_KEY=...` y exponerla al frontend como
    # NEXT_PUBLIC_API_KEY. No es auth por usuario, pero saca a la API de estar
    # 100% abierta a internet/escáneres.
    api_key: str = ""
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/talenscan"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: object) -> object:
        if isinstance(value, str):
            return _normalize_database_url(value)
        return value
    max_upload_size_mb: int = 12
    storage_base_url: str = "local://candidate-documents"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 120.0
    openai_max_retries: int = 1

    apify_token: str = ""
    # harvestapi es Pay-Per-Result: funciona en plan free vía API.
    # dev_fusion era rental (bloqueado en free para API).
    apify_linkedin_actor: str = "harvestapi/linkedin-profile-scraper"
    apify_timeout_seconds: float = 180.0

    # Decision Room: HMAC para firmar session tokens del cliente tras validar
    # el código de 6 dígitos. En prod debe ir por fly secrets; en dev queda fijo
    # para que las sesiones sobrevivan reinicios del worker.
    decision_room_secret: str = "decision-room-dev-secret-change-me"
    decision_room_session_ttl_seconds: int = 60 * 60 * 4  # 4h por sesión validada

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def apify_enabled(self) -> bool:
        return bool(self.apify_token)


settings = Settings()
