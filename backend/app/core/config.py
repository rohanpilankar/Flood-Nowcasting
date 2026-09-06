import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "FloodWatch AI"
    API_V1_STR: str = "/api/v1"
    SIH_PROJECT_CODE: str = "SIH26085"
    STUDY_AREA: str = "Greater Mumbai / Brihanmumbai Municipal Corporation (BMC)"
    MODEL_VERSION: str = "XGBoost-v2.0-Mumbai"
    DATA_MODE: str = "mumbai_real_pipeline"
    USE_DEVELOPMENT_FALLBACK: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:4200", "http://127.0.0.1:4200", "*"]
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sih26085-mumbai-floodwatch-ai-secret-key-2026-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/floodwatch.db")

    # Environment & Demo Seed
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ENABLE_DEMO_SEED: bool = os.getenv("ENABLE_DEMO_SEED", "true").lower() == "true"

    # Alert Geofence & Location Retention
    ALERT_ZONE_BUFFER_METERS: float = 500.0
    ALERT_COOLDOWN_MINUTES: int = 30
    LOCATION_MAX_AGE_HOURS: int = 4
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
