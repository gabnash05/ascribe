from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    supabase_storage_bucket: str

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # OpenAI
    openai_api_key: str = ""

    # App
    secret_key: str
    environment: str = "dev"
    frontend_url: str = "http://localhost:5173"

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str = "./model_cache"


settings = Settings()
