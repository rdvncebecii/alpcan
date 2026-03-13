from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "AlpCAN API"
    app_version: str = "0.2.0"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://alpcan:alpcan_secret@db:5432/alpcan"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Auth
    secret_key: str = "change-this-to-a-random-secret-key"
    access_token_expire_minutes: int = 1440  # 24 hours

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "https://alpcan.alpiss.net"]

    # Orthanc
    orthanc_url: str = "http://orthanc:8042"

    # ML
    model_weights_dir: str = "/app/ml/weights"
    inference_device: str = "cpu"
    ml_config_path: str = "/app/ml/configs/models.yaml"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def ml_config(self) -> dict:
        """ML model konfigürasyonunu YAML dosyasından yükle (lazy, cached)."""
        return _load_ml_config(self.ml_config_path)


@lru_cache(maxsize=1)
def _load_ml_config(config_path: str) -> dict:
    """YAML config dosyasını oku ve cache'le."""
    path = Path(config_path)
    if not path.exists():
        return {}
    import yaml

    with open(path) as f:
        return yaml.safe_load(f) or {}


settings = Settings()
