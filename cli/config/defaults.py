"""Default configuration factory."""

from .schema import (
    QwenConfig,
    ProjectConfig,
    RulesConfig,
    SafetyConfig,
    HooksConfig,
    ContextConfig,
)


def get_default_config() -> QwenConfig:
    """Get default configuration with sensible defaults.
    
    Returns:
        QwenConfig with default values for all settings
    """
    return QwenConfig(
        project=ProjectConfig(
            name="my-project",
            type="python",
            version="1.0.0",
            description="Project managed by qwen-dev-cli"
        ),
        rules=RulesConfig(
            rules=[
                "Use type hints for all functions",
                "Write docstrings in Google style",
                "Follow PEP 8 style guide",
                "Keep functions small and focused",
                "Use meaningful variable names",
            ],
            style_guide="PEP 8",
            max_line_length=100,
            use_type_hints=True,
            docstring_style="google"
        ),
        safety=SafetyConfig(
            allowed_paths=["./"],
            dangerous_commands=[
                "rm -rf",
                "chmod 777",
                "dd if=",
                "mkfs",
                "> /dev/",
            ],
            require_approval=[
                "git push",
                "docker run",
                "pip install",
                "npm install",
            ],
            max_file_size_mb=10,
            enable_sandbox=False
        ),
        hooks=HooksConfig(
            post_write=[],
            post_edit=[],
            post_delete=[],
            pre_commit=[]
        ),
        context=ContextConfig(
            max_tokens=32000,
            include_git=True,
            include_tests=True,
            include_docs=True,
            exclude_patterns=[
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/venv/**",
                "**/.venv/**",
                "**/.git/**",
                "**/*.pyc",
                "**/.DS_Store",
            ],
            file_extensions=[
                ".py", ".js", ".ts", ".jsx", ".tsx",
                ".rs", ".go", ".java", ".cpp", ".c",
                ".md", ".txt", ".yaml", ".yml", ".json",
            ]
        )
    )


def get_python_config() -> QwenConfig:
    """Get Python-specific configuration preset."""
    config = get_default_config()
    config.project.type = "python"
    config.rules.rules = [
        "Use type hints for all functions and class attributes",
        "Write docstrings in Google style",
        "Follow PEP 8 style guide (max line length: 100)",
        "Use f-strings for string formatting",
        "Prefer pathlib.Path over os.path",
        "Use dataclasses for data structures",
        "Handle exceptions explicitly",
    ]
    config.hooks.post_write = [
        "ruff check {file}",
        "black {file}",
    ]
    config.hooks.post_edit = [
        "ruff format {file}",
    ]
    config.hooks.pre_commit = [
        "pytest tests/",
        "ruff check .",
        "mypy .",
    ]
    return config


def get_javascript_config() -> QwenConfig:
    """Get JavaScript/TypeScript-specific configuration preset."""
    config = get_default_config()
    config.project.type = "javascript"
    config.rules.rules = [
        "Use TypeScript for type safety",
        "Follow ESLint recommended rules",
        "Use async/await over callbacks",
        "Prefer const over let, avoid var",
        "Use arrow functions for callbacks",
        "Document complex functions with JSDoc",
    ]
    config.hooks.post_write = [
        "eslint {file}",
        "prettier --write {file}",
    ]
    config.hooks.pre_commit = [
        "npm test",
        "eslint .",
    ]
    config.context.file_extensions = [
        ".js", ".ts", ".jsx", ".tsx",
        ".json", ".md",
    ]
    return config


def get_rust_config() -> QwenConfig:
    """Get Rust-specific configuration preset."""
    config = get_default_config()
    config.project.type = "rust"
    config.rules.rules = [
        "Follow Rust naming conventions",
        "Use Result<T, E> for error handling",
        "Document public APIs with doc comments",
        "Run clippy lints",
        "Use cargo fmt for formatting",
    ]
    config.hooks.post_write = [
        "cargo fmt {file}",
        "cargo clippy -- -D warnings",
    ]
    config.hooks.pre_commit = [
        "cargo test",
        "cargo clippy",
    ]
    config.context.file_extensions = [
        ".rs", ".toml", ".md",
    ]
    return config
