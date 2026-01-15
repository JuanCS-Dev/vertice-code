"""
Configuration management for Vertice CLI.
"""

from typing import Optional


class Config:
    """Global configuration."""

    def __init__(self):
        self.debug = False
        self.log_level = "INFO"
        self.model_name = "gpt-4"
        self.api_key = ""
        self.max_tokens = 1000

    @classmethod
    def load(cls) -> "Config":
        """Load configuration."""
        return cls()
