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
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # Server Configuration
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://0.0.0.0:3000"]
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"])

    # PostgreSQL Configuration
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="dlp_user")
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(default="cybersentinel_dlp")
    POSTGRES_POOL_SIZE: int = Field(default=20)
    POSTGRES_MAX_OVERFLOW: int = Field(default=10)

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # MongoDB Configuration
    MONGODB_HOST: str = Field(default="localhost")
    MONGODB_PORT: int = Field(default=27017)
    MONGODB_USER: str = Field(default="dlp_user")
    MONGODB_PASSWORD: str = Field(...)
    MONGODB_DB: str = Field(default="cybersentinel_dlp")
    MONGODB_MAX_POOL_SIZE: int = Field(default=100)

    @property
    def MONGODB_URL(self) -> str:
        """Construct MongoDB connection URL"""
        return (
            f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
            f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB}"
            f"?authSource=admin"
        )

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_POOL_SIZE: int = Field(default=10)

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: Optional[str] = Field(default=None)

    # Email Configuration (for alerts)
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_FROM: str = Field(default="dlp@cybersentinel.local")

    # Wazuh Integration
    WAZUH_HOST: str = Field(default="localhost")
    WAZUH_PORT: int = Field(default=1514)
    WAZUH_PROTOCOL: str = Field(default="udp")
    WAZUH_API_URL: Optional[str] = Field(default=None)
    WAZUH_API_USER: Optional[str] = Field(default=None)
    WAZUH_API_PASSWORD: Optional[str] = Field(default=None)

    # ML Configuration
    ML_MODEL_PATH: str = Field(default="./ml/models")
    ML_INFERENCE_BATCH_SIZE: int = Field(default=32)
    ML_CONFIDENCE_THRESHOLD: float = Field(default=0.75)

    # DLP Configuration
    DLP_MAX_FILE_SIZE_MB: int = Field(default=100)
    DLP_SCAN_TIMEOUT_SECONDS: int = Field(default=30)
    DLP_QUARANTINE_PATH: str = Field(default="./quarantine")

    # Classification Thresholds
    CLASSIFICATION_HIGH_RISK_THRESHOLD: float = Field(default=0.85)
    CLASSIFICATION_MEDIUM_RISK_THRESHOLD: float = Field(default=0.60)

    # Monitoring & Metrics
    METRICS_ENABLED: bool = Field(default=True)
    HEALTH_CHECK_INTERVAL: int = Field(default=30)

    # Feature Flags
    FEATURE_ML_CLASSIFICATION: bool = Field(default=True)
    FEATURE_REAL_TIME_BLOCKING: bool = Field(default=True)
    FEATURE_CLOUD_CONNECTORS: bool = Field(default=True)

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
