"""
Validation utilities for TwitterAPI.io client.

ابزارهای اعتبارسنجی برای کلاینت TwitterAPI.io
"""

import re
from typing import Any, Dict, List, Optional, Union

from lib.twitter_api.exceptions import TwitterAPIValidationError


def validate_api_key(api_key: str) -> None:
    """
    Validate API key format.

    Args:
        api_key: API key to validate

    Raises:
        TwitterAPIValidationError: If API key is invalid
    """
    if not api_key:
        raise TwitterAPIValidationError("API key cannot be empty")

    if not isinstance(api_key, str):
        raise TwitterAPIValidationError("API key must be a string")

    if len(api_key) < 10:  # Assuming API keys are at least 10 characters
        raise TwitterAPIValidationError("API key is too short")


def validate_required_params(params: Dict[str, Any], required_params: List[str]) -> None:
    """
    Validate that all required parameters are present and not empty.

    Args:
        params: Dictionary of parameters
        required_params: List of required parameter names

    Raises:
        TwitterAPIValidationError: If any required parameter is missing or empty
    """
    for param in required_params:
        if param not in params:
            raise TwitterAPIValidationError(f"Missing required parameter: {param}")

        if params[param] is None or (isinstance(params[param], str) and params[param].strip() == ""):
            raise TwitterAPIValidationError(f"Required parameter cannot be empty: {param}")


def validate_numeric_param(value: Any, param_name: str, min_value: Optional[Union[int, float]] = None,
                         max_value: Optional[Union[int, float]] = None) -> int:
    """
    Validate numeric parameter.

    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        Validated numeric value (converted to int if string)

    Raises:
        TwitterAPIValidationError: If validation fails
    """
    # Try to convert string to int if needed
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            raise TwitterAPIValidationError(f"Parameter {param_name} must be a valid number")

    # Check if value is a number
    if not isinstance(value, (int, float)):
        raise TwitterAPIValidationError(f"Parameter {param_name} must be a number")

    # Check minimum value
    if min_value is not None and value < min_value:
        raise TwitterAPIValidationError(f"Parameter {param_name} must be at least {min_value}")

    # Check maximum value
    if max_value is not None and value > max_value:
        raise TwitterAPIValidationError(f"Parameter {param_name} must be at most {max_value}")

    return int(value) if isinstance(value, float) and value.is_integer() else value


def validate_string_param(value: Any, param_name: str, max_length: Optional[int] = None,
                        pattern: Optional[str] = None) -> str:
    """
    Validate string parameter.

    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages
        max_length: Maximum allowed length
        pattern: Regex pattern to match

    Returns:
        Validated string value

    Raises:
        TwitterAPIValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise TwitterAPIValidationError(f"Parameter {param_name} must be a string")

    if max_length is not None and len(value) > max_length:
        raise TwitterAPIValidationError(f"Parameter {param_name} must be at most {max_length} characters long")

    if pattern is not None and not re.match(pattern, value):
        raise TwitterAPIValidationError(f"Parameter {param_name} has invalid format")

    return value


def validate_boolean_param(value: Any, param_name: str) -> bool:
    """
    Validate boolean parameter.

    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages

    Returns:
        Validated boolean value (converted from string if needed)

    Raises:
        TwitterAPIValidationError: If validation fails
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes", "y"):
            return True
        elif value.lower() in ("false", "0", "no", "n"):
            return False

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    raise TwitterAPIValidationError(f"Parameter {param_name} must be a boolean value")


def validate_enum_param(value: Any, param_name: str, allowed_values: List[Any]) -> Any:
    """
    Validate parameter against a list of allowed values.

    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages
        allowed_values: List of allowed values

    Returns:
        Validated value

    Raises:
        TwitterAPIValidationError: If validation fails
    """
    if value not in allowed_values:
        values_str = ", ".join(str(v) for v in allowed_values)
        raise TwitterAPIValidationError(f"Parameter {param_name} must be one of: {values_str}")

    return value


def validate_cursor(cursor: Optional[str] = None) -> str:
    """
    Validate pagination cursor.

    Args:
        cursor: Cursor value

    Returns:
        Validated cursor (empty string if None)
    """
    if cursor is None:
        return ""

    if not isinstance(cursor, str):
        raise TwitterAPIValidationError("Cursor must be a string")

    return cursor