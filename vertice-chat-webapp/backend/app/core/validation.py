"""
Input validation utilities
Provides security-focused input validation for user data

Reference: OWASP Input Validation Cheat Sheet
"""

import re
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, validator


class ValidationError(Exception):
    """Custom validation error"""

    pass


class InputValidator:
    """Input validation utilities"""

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"data:",  # Data URLs (can contain scripts)
        r"vbscript:",  # VBScript
        r"on\w+\s*=",  # Event handlers
        r"<\w+[^>]*\son\w+\s*=",  # HTML with event handlers
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r";\s*(drop|delete|update|insert|alter|create|truncate)",
        r"union\s+select",
        r"--",  # SQL comments
        r"/\*.*?\*/",  # Block comments
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()<>]",  # Shell metacharacters
        r"\$\{.*\}",  # Shell variable expansion
        r"`.*`",  # Command substitution
    ]

    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """
        Sanitize text input

        Args:
            text: Input text
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            ValidationError: If input is invalid
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")

        if len(text) > max_length:
            raise ValidationError(f"Text too long (max {max_length} characters)")

        # Remove null bytes
        text = text.replace("\x00", "")

        # Check for dangerous patterns
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError("Potentially dangerous content detected")

        return text.strip()

    @staticmethod
    def validate_code_input(code: str, language: Optional[str] = None) -> str:
        """
        Validate code input for execution

        Args:
            code: Code to validate
            language: Programming language

        Returns:
            Validated code

        Raises:
            ValidationError: If code is invalid
        """
        code = InputValidator.sanitize_text(code, max_length=50000)

        # Check for command injection in code
        for pattern in InputValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, code):
                raise ValidationError("Potentially dangerous code detected")

        # Language-specific validations
        if language == "python":
            InputValidator._validate_python_code(code)
        elif language == "javascript":
            InputValidator._validate_javascript_code(code)

        return code

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate filename for security

        Args:
            filename: Filename to validate

        Returns:
            Validated filename

        Raises:
            ValidationError: If filename is invalid
        """
        if not filename or not isinstance(filename, str):
            raise ValidationError("Invalid filename")

        # Remove path separators
        filename = filename.replace("/", "").replace("\\", "").replace("..", "")

        # Check length
        if len(filename) > 255:
            raise ValidationError("Filename too long")

        # Allow only safe characters
        if not re.match(r"^[a-zA-Z0-9._-]+$", filename):
            raise ValidationError("Filename contains invalid characters")

        # Prevent hidden files
        if filename.startswith("."):
            raise ValidationError("Hidden files not allowed")

        return filename

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL for security

        Args:
            url: URL to validate

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise ValidationError("Invalid URL")

        # Check length
        if len(url) > 2000:
            raise ValidationError("URL too long")

        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(url):
            raise ValidationError("Invalid URL format")

        return url

    @staticmethod
    def _validate_python_code(code: str) -> None:
        """Validate Python code for security"""
        # Check for dangerous imports
        dangerous_imports = [
            "os.system",
            "subprocess.call",
            "subprocess.run",
            "eval",
            "exec",
            "__import__",
            "importlib",
        ]

        for dangerous in dangerous_imports:
            if dangerous in code:
                raise ValidationError(f"Dangerous import detected: {dangerous}")

    @staticmethod
    def _validate_javascript_code(code: str) -> None:
        """Validate JavaScript code for security"""
        # Check for dangerous functions
        dangerous_functions = [
            "eval",
            "Function",
            "setTimeout",
            "setInterval",
            "XMLHttpRequest",
            "fetch",
            "require",
            "import",
        ]

        for dangerous in dangerous_functions:
            if dangerous in code:
                raise ValidationError(f"Dangerous function detected: {dangerous}")


# Pydantic models for API validation


class SafeMessage(BaseModel):
    """Validated chat message"""

    role: str
    content: str

    @validator("role")
    def validate_role(cls, v):
        allowed_roles = ["user", "assistant", "system"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v

    @validator("content")
    def validate_content(cls, v):
        return InputValidator.sanitize_text(v, max_length=10000)


class SafeArtifactRequest(BaseModel):
    """Validated artifact request"""

    name: str
    content: str
    language: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        return InputValidator.validate_filename(v)

    @validator("content")
    def validate_content(cls, v):
        return InputValidator.validate_code_input(v)


class SafeCommandRequest(BaseModel):
    """Validated command request"""

    command: str
    args: Optional[List[str]] = []

    @validator("command")
    def validate_command(cls, v):
        return InputValidator.sanitize_text(v, max_length=100)

    @validator("args")
    def validate_args(cls, v):
        if len(v) > 10:
            raise ValueError("Too many arguments")
        for arg in v:
            if len(arg) > 500:
                raise ValueError("Argument too long")
            InputValidator.sanitize_text(arg, max_length=500)
        return v


# FastAPI dependency functions


async def validate_message(message: Dict[str, Any]) -> SafeMessage:
    """Validate chat message for FastAPI endpoints"""
    try:
        return SafeMessage(**message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid message: {str(e)}")


async def validate_artifact_request(request: Dict[str, Any]) -> SafeArtifactRequest:
    """Validate artifact request for FastAPI endpoints"""
    try:
        return SafeArtifactRequest(**request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid artifact request: {str(e)}")


async def validate_command_request(request: Dict[str, Any]) -> SafeCommandRequest:
    """Validate command request for FastAPI endpoints"""
    try:
        return SafeCommandRequest(**request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid command request: {str(e)}")
