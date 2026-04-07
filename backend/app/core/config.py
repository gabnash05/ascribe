from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    supabase_storage_bucket: str

    worker_database_url: str
    worker_db_host: str = ""
    worker_db_port: int = 6543
    worker_db_user: str = ""
    worker_db_password: str = ""
    worker_db_name: str = "postgres"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # App
    secret_key: str
    environment: str = "dev"
    frontend_url: str = "http://localhost:5173"

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str = "./model_cache"

    # File Uploads
    max_file_size_bytes: int = 52428800  # 50 MB


settings = Settings()
