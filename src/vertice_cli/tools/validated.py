"""
Validated tool base class.

Boris Cherny: "Validate early, fail fast with clear feedback."

This module provides a base class that automatically validates
tool inputs using our validation system before execution.
"""

from typing import Dict, Any
from abc import ABC, abstractmethod

from .base import Tool, ToolResult
from ..core.validation import (
    InputValidator as Validator,
    ValidationResult as ValidationResultImpl,
)
from ..core.errors import ValidationError as ErrorValidationError


class ValidatedTool(Tool, ABC):
    """
    Base class for tools with automatic input validation.

    Subclasses should:
    1. Define validators in get_validators()
    2. Implement _execute_validated() instead of execute()

    The base class will automatically validate inputs before
    calling _execute_validated().
    """

    def get_validators(self) -> Dict[str, Validator]:
        """
        Return validators for each parameter.

        Returns:
            Dict mapping parameter name to Validator instance

        Example:
            return {
                'path': Required('path'),
                'content': TypeCheck(str, 'content')
            }
        """
        return {}

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute tool with validation.

        This wraps the actual execution with validation.
        Subclasses should implement _execute_validated() instead.
        """
        # Validate inputs
        validation_result = self._validate_inputs(kwargs)

        if not validation_result.is_valid:
            # Return validation errors
            error_msg = "\n".join(validation_result.errors)
            return ToolResult(
                success=False,
                error=f"Validation failed:\n{error_msg}",
                metadata={
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                },
            )

        # Show warnings if any
        if validation_result.warnings:
            # Could log or display warnings here
            pass

        # Execute the actual tool logic
        try:
            return await self._execute_validated(**kwargs)
        except ErrorValidationError as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"error_type": "validation", "recoverable": e.recoverable},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Execution failed: {e}",
                metadata={"error_type": "execution", "exception": type(e).__name__},
            )

    @abstractmethod
    async def _execute_validated(self, **kwargs) -> ToolResult:
        """
        Execute tool logic after validation.

        Subclasses must implement this method.
        All inputs are guaranteed to be valid when this is called.
        """
        raise NotImplementedError(f"{self.__class__.__name__}._execute_validated() not implemented")

    def _validate_inputs(self, inputs: Dict[str, Any]) -> ValidationResultImpl:
        """
        Validate inputs against defined validators AND schema.

        P2.3 FIX: Now validates against self.parameters schema.
        Source: Scalify AI - "Type checking confirms every argument matches required type"

        Args:
            inputs: Input parameters to validate

        Returns:
            ValidationResult with errors/warnings
        """
        all_errors = []
        all_warnings = []

        # P2.3: First validate against schema (self.parameters)
        schema_errors = self._validate_against_schema(inputs)
        all_errors.extend(schema_errors)

        # Then validate with custom validators (validators are callables)
        validators = self.get_validators()
        for param_name, validator in validators.items():
            value = inputs.get(param_name)
            # Validators are callable (use __call__), not objects with .validate()
            param_result = validator(value)

            if not param_result.is_valid:
                for error in param_result.errors:
                    all_errors.append(f"{param_name}: {error}")

            for warning in param_result.warnings:
                all_warnings.append(f"{param_name}: {warning}")

        # Return combined result
        if all_errors:
            return ValidationResultImpl.failure(all_errors)
        return ValidationResultImpl.success(inputs, warnings=all_warnings)

    def _validate_against_schema(self, inputs: Dict[str, Any]) -> list:
        """
        P2.3 FIX: Validate inputs against self.parameters schema.

        Checks:
        1. Required parameters are present
        2. Types match schema (string, integer, boolean, array, object)

        Source: Agenta - "Use jsonschema validation to catch ValidationErrors"

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        for param_name, param_spec in self.parameters.items():
            value = inputs.get(param_name)
            is_required = param_spec.get("required", False)
            expected_type = param_spec.get("type", "string")

            # Check required
            if is_required and value is None:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue

            # Skip type check if value is None and not required
            if value is None:
                continue

            # Type validation
            type_valid = self._check_type(value, expected_type)
            if not type_valid:
                actual_type = type(value).__name__
                errors.append(
                    f"Parameter '{param_name}' must be {expected_type}, got {actual_type}"
                )

            # Enum validation (if specified)
            if "enum" in param_spec and value not in param_spec["enum"]:
                allowed = ", ".join(str(v) for v in param_spec["enum"])
                errors.append(f"Parameter '{param_name}' must be one of [{allowed}], got '{value}'")

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # Unknown type, allow
        return isinstance(value, expected)


# Helper function for quick validation
def validate_tool_inputs(
    inputs: Dict[str, Any], validators: Dict[str, Validator]
) -> ValidationResultImpl:
    """
    Validate tool inputs standalone (without ValidatedTool class).

    Args:
        inputs: Input parameters
        validators: Validators for each parameter

    Returns:
        ValidationResult

    Example:
        validators = {
            'path': Required('path'),
            'mode': OneOf(['r', 'w', 'a'], 'mode')
        }
        result = validate_tool_inputs(inputs, validators)
        if not result.is_valid:
            raise ValidationError(result.errors[0])
    """
    all_errors = []
    all_warnings = []

    for param_name, validator in validators.items():
        value = inputs.get(param_name)
        # Validators are callable (use __call__), not objects with .validate()
        param_result = validator(value)

        if not param_result.is_valid:
            for error in param_result.errors:
                all_errors.append(f"{param_name}: {error}")

        for warning in param_result.warnings:
            all_warnings.append(f"{param_name}: {warning}")

    if all_errors:
        return ValidationResultImpl.failure(all_errors)
    return ValidationResultImpl.success(inputs, warnings=all_warnings)


__all__ = [
    "ValidatedTool",
    "validate_tool_inputs",
]
