"""
LSP Configuration - Language server configurations.

Contains:
- LanguageServerConfig: Configuration for a language server
- DEFAULT_LANGUAGE_SERVERS: Built-in configurations
"""

import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LanguageServerConfig:
    """Configuration for a language server."""
    language: str
    command: List[str]
    file_extensions: List[str]
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    root_markers: List[str] = field(default_factory=list)

    def is_installed(self) -> bool:
        """Check if the language server is installed."""
        if not self.command:
            return False
        return shutil.which(self.command[0]) is not None


# Default language server configurations
DEFAULT_LANGUAGE_SERVERS: Dict[str, LanguageServerConfig] = {
    "python": LanguageServerConfig(
        language="python",
        command=["pylsp"],
        file_extensions=[".py", ".pyi"],
        root_markers=["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
        settings={
            "pylsp": {
                "plugins": {
                    "pycodestyle": {"enabled": False},
                    "mccabe": {"enabled": False},
                    "pyflakes": {"enabled": True},
                    "rope_autoimport": {"enabled": True},
                }
            }
        },
    ),
    "typescript": LanguageServerConfig(
        language="typescript",
        command=["typescript-language-server", "--stdio"],
        file_extensions=[".ts", ".tsx", ".js", ".jsx"],
        root_markers=["tsconfig.json", "jsconfig.json", "package.json"],
    ),
    "javascript": LanguageServerConfig(
        language="javascript",
        command=["typescript-language-server", "--stdio"],
        file_extensions=[".js", ".jsx", ".mjs"],
        root_markers=["package.json", "jsconfig.json"],
    ),
    "go": LanguageServerConfig(
        language="go",
        command=["gopls"],
        file_extensions=[".go"],
        root_markers=["go.mod", "go.sum"],
    ),
    "rust": LanguageServerConfig(
        language="rust",
        command=["rust-analyzer"],
        file_extensions=[".rs"],
        root_markers=["Cargo.toml"],
    ),
    "java": LanguageServerConfig(
        language="java",
        command=["jdtls"],
        file_extensions=[".java"],
        root_markers=["pom.xml", "build.gradle", "build.gradle.kts"],
    ),
    "c": LanguageServerConfig(
        language="c",
        command=["clangd"],
        file_extensions=[".c", ".h"],
        root_markers=["compile_commands.json", "CMakeLists.txt", "Makefile"],
    ),
    "cpp": LanguageServerConfig(
        language="cpp",
        command=["clangd"],
        file_extensions=[".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
        root_markers=["compile_commands.json", "CMakeLists.txt", "Makefile"],
    ),
}
