"""
Secrets Manager - CODE_CONSTITUTION Compliant.

Artigo VI: Security Standards - Never hardcode secrets.

Provides secure access to environment variables and secrets
with validation, caching, and clear error messages.
"""

import os
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class SecretConfig:
    """Configuration for secrets management."""

    source: str = "env"  # "env", "vault", "aws_secrets_manager"
    prefix: str = ""  # Optional prefix for all keys
    cache_enabled: bool = True


class SecretsManager:
    """
    Thread-safe secrets manager with caching.

    Usage:
        from vertice_core.config import secrets

        # Get required secret (raises if missing)
        api_key = secrets.get("ANTHROPIC_API_KEY")

        # Get optional secret
        optional_key = secrets.get("DEBUG_KEY", required=False)

        # Validate multiple secrets at once
        status = secrets.validate_required([
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
        ])
    """

    def __init__(self, config: Optional[SecretConfig] = None):
        self.config = config or SecretConfig()
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, key: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value securely.

        Args:
            key: The secret key (without prefix)
            required: If True, raises ValueError when not found
            default: Default value if not found and not required

        Returns:
            The secret value, or default/None if not found

        Raises:
            ValueError: If required=True and secret not found
        """
        full_key = f"{self.config.prefix}{key}" if self.config.prefix else key

        # Check cache first (thread-safe)
        if self.config.cache_enabled:
            with self._lock:
                if full_key in self._cache:
                    return self._cache[full_key]

        # Get from environment
        value = os.getenv(full_key)

        if value is None:
            if required:
                raise ValueError(
                    f"Required secret '{full_key}' not found. "
                    f"Set it in environment or .env file. "
                    f"See .env.example for reference."
                )
            return default

        # Cache the value (thread-safe)
        if self.config.cache_enabled:
            with self._lock:
                self._cache[full_key] = value

        return value

    def get_or_raise(self, key: str, error_message: Optional[str] = None) -> str:
        """
        Get a required secret, with custom error message.

        Args:
            key: The secret key
            error_message: Custom error message if not found

        Returns:
            The secret value

        Raises:
            ValueError: If secret not found
        """
        value = self.get(key, required=False)
        if value is None:
            raise ValueError(
                error_message or f"Secret '{key}' is required but not set. Check your .env file."
            )
        return value

    def validate_required(self, keys: list[str]) -> dict[str, bool]:
        """
        Validate that all required secrets exist.

        Args:
            keys: List of secret keys to validate

        Returns:
            Dict mapping key to True (exists) or False (missing)
        """
        results = {}
        for key in keys:
            try:
                self.get(key, required=True)
                results[key] = True
            except ValueError:
                results[key] = False
        return results

    def get_provider_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific LLM provider.

        Handles common naming variations.

        Args:
            provider: Provider name (anthropic, google, openai, etc.)

        Returns:
            API key or None
        """
        provider_keys = {
            "anthropic": ["ANTHROPIC_API_KEY"],
            "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "azure": ["AZURE_OPENAI_KEY"],
            "groq": ["GROQ_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
            "cerebras": ["CEREBRAS_API_KEY"],
        }

        key_names = provider_keys.get(provider.lower(), [f"{provider.upper()}_API_KEY"])

        for key_name in key_names:
            value = self.get(key_name, required=False)
            if value:
                return value

        return None

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        with self._lock:
            self._cache.clear()

    def has_any_provider(self) -> bool:
        """Check if at least one LLM provider is configured."""
        providers = ["anthropic", "google", "openai", "azure", "groq", "mistral"]
        return any(self.get_provider_key(p) for p in providers)


# Global singleton instance
secrets = SecretsManager()
