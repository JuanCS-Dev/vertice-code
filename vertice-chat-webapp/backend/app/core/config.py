"""
Application Configuration using Pydantic Settings
Reference: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Vertice Chat"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://app.vertice.ai"]
    CORS_ORIGIN_REGEX: Optional[str] = r"https://vertice-frontend-.*-uc\.a\.run\.app"

    # LLM API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Prompt Caching Config
    # Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    ENABLE_PROMPT_CACHING: bool = True
    CACHE_MIN_TOKENS: int = 1024  # Minimum for Anthropic caching
    CACHE_TTL_SECONDS: int = 300  # 5 minutes (Anthropic default)

    # Cost Management
    MAX_TOKENS_PER_REQUEST: int = 8192
    DAILY_TOKEN_LIMIT_PER_USER: int = 100_000

    # Database (Neon PostgreSQL)
    DATABASE_URL: Optional[str] = None

    # Redis (Upstash)
    REDIS_URL: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50

    # S3 Compatible Storage (for artifacts)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "vertice-artifacts"

    # Observability
    SENTRY_DSN: Optional[str] = None
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None

    # Sandboxing
    ENABLE_SANDBOXING: bool = True
    SANDBOX_ALLOWED_DIRS: List[str] = ["/tmp/workspace"]
    SANDBOX_ALLOWED_HOSTS: List[str] = ["github.com", "api.anthropic.com"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # Google Identity (Firebase Auth)
    FIREBASE_PROJECT_ID: Optional[str] = "vertice-ai"
    GOOGLE_CLOUD_PROJECT: Optional[str] = "vertice-ai"

    # Stripe Billing
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Encryption (GDPR)
    # Master key for deriving workspace encryption keys
    # MUST be a 32-byte base64 encoded string
    GDPR_MASTER_KEY: Optional[str] = None

    # Google Cloud KMS (GDPR master key protection)
    # KMS_KEY_NAME example:
    #   projects/<project>/locations/<location>/keyRings/<ring>/cryptoKeys/<key>
    KMS_KEY_NAME: Optional[str] = None
    # Base64 ciphertext blob that decrypts to the 32-byte master key.
    GDPR_MASTER_KEY_CIPHERTEXT: Optional[str] = None

    # Billing Plans (Stripe Price IDs)
    STRIPE_PRICE_FREEMIUM: str = "price_freemium_monthly"
    STRIPE_PRICE_PRO: str = "price_pro_monthly"
    STRIPE_PRICE_ENTERPRISE: str = "price_enterprise_monthly"

    # Usage Metering
    USAGE_REPORT_INTERVAL_MINUTES: int = 15
    USAGE_BATCH_SIZE: int = 100

    # Frontend URL for Stripe redirects
    FRONTEND_URL: str = "http://localhost:3000"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
