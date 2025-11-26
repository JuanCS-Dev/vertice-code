"""Project configuration system for qwen-dev-cli.

This module provides YAML-based project configuration with:
- Custom coding rules and conventions
- Safety settings (allowed paths, dangerous commands)
- Hook system (post-write, post-edit, pre-commit)
- Context management (token limits, file patterns)
"""

from .schema import (
    QwenConfig,
    ProjectConfig,
    RulesConfig,
    SafetyConfig,
    HooksConfig,
    ContextConfig,
)
from .loader import ConfigLoader
from .defaults import get_default_config

__all__ = [
    'QwenConfig',
    'ProjectConfig',
    'RulesConfig',
    'SafetyConfig',
    'HooksConfig',
    'ContextConfig',
    'ConfigLoader',
    'get_default_config',
]
