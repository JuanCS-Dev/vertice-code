"""
VERTICE Core Configuration Module.

Provides secure secrets management and configuration.
"""

from .secrets import SecretsManager, SecretConfig, secrets

__all__ = ["SecretsManager", "SecretConfig", "secrets"]
