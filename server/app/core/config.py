"""
Configuration Management
Centralized configuration using Pydantic Settings
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    # Application Info
    PROJECT_NAME: str = "CyberSentinel DLP"
    PROJECT_DESCRIPTION: str = "Enterprise Data Loss Prevention Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://0.0.0.0:3000"],
        env="CORS_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # PostgreSQL Configuration
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(default="dlp_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="cybersentinel_dlp", env="POSTGRES_DB")
    POSTGRES_POOL_SIZE: int = Field(default=20, env="POSTGRES_POOL_SIZE")
    POSTGRES_MAX_OVERFLOW: int = Field(default=10, env="POSTGRES_MAX_OVERFLOW")

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # MongoDB Configuration
    MONGODB_HOST: str = Field(default="localhost", env="MONGODB_HOST")
    MONGODB_PORT: int = Field(default=27017, env="MONGODB_PORT")
    MONGODB_USER: str = Field(default="dlp_user", env="MONGODB_USER")
    MONGODB_PASSWORD: str = Field(..., env="MONGODB_PASSWORD")
    MONGODB_DB: str = Field(default="cybersentinel_dlp", env="MONGODB_DB")
    MONGODB_MAX_POOL_SIZE: int = Field(default=100, env="MONGODB_MAX_POOL_SIZE")

    @property
    def MONGODB_URL(self) -> str:
        """Construct MongoDB connection URL"""
        return (
            f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
            f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"
            f"?authSource=admin"
        )

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")

    # Email Configuration (for alerts)
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM: str = Field(default="dlp@cybersentinel.local", env="SMTP_FROM")

    # Wazuh Integration
    WAZUH_HOST: str = Field(default="localhost", env="WAZUH_HOST")
    WAZUH_PORT: int = Field(default=1514, env="WAZUH_PORT")
    WAZUH_PROTOCOL: str = Field(default="udp", env="WAZUH_PROTOCOL")
    WAZUH_API_URL: Optional[str] = Field(default=None, env="WAZUH_API_URL")
    WAZUH_API_USER: Optional[str] = Field(default=None, env="WAZUH_API_USER")
    WAZUH_API_PASSWORD: Optional[str] = Field(default=None, env="WAZUH_API_PASSWORD")

    # ML Configuration
    ML_MODEL_PATH: str = Field(default="./ml/models", env="ML_MODEL_PATH")
    ML_INFERENCE_BATCH_SIZE: int = Field(default=32, env="ML_INFERENCE_BATCH_SIZE")
    ML_CONFIDENCE_THRESHOLD: float = Field(default=0.75, env="ML_CONFIDENCE_THRESHOLD")

    # DLP Configuration
    DLP_MAX_FILE_SIZE_MB: int = Field(default=100, env="DLP_MAX_FILE_SIZE_MB")
    DLP_SCAN_TIMEOUT_SECONDS: int = Field(default=30, env="DLP_SCAN_TIMEOUT_SECONDS")
    DLP_QUARANTINE_PATH: str = Field(default="./quarantine", env="DLP_QUARANTINE_PATH")

    # Classification Thresholds
    CLASSIFICATION_HIGH_RISK_THRESHOLD: float = Field(default=0.85, env="CLASSIFICATION_HIGH_RISK_THRESHOLD")
    CLASSIFICATION_MEDIUM_RISK_THRESHOLD: float = Field(default=0.60, env="CLASSIFICATION_MEDIUM_RISK_THRESHOLD")

    # Monitoring & Metrics
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # Feature Flags
    FEATURE_ML_CLASSIFICATION: bool = Field(default=True, env="FEATURE_ML_CLASSIFICATION")
    FEATURE_REAL_TIME_BLOCKING: bool = Field(default=True, env="FEATURE_REAL_TIME_BLOCKING")
    FEATURE_CLOUD_CONNECTORS: bool = Field(default=True, env="FEATURE_CLOUD_CONNECTORS")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from comma-separated string"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
