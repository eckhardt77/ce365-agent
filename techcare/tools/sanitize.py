"""
TechCare Bot - Input Sanitization for Command Execution

Prevents command injection in subprocess calls (PowerShell, AppleScript, Shell).
"""

import re
from pathlib import Path


def sanitize_powershell_string(value: str) -> str:
    """
    Sanitizes a string for safe use in PowerShell single-quoted strings.
    In PowerShell, single-quoted strings only need ' escaped as ''.
    """
    return value.replace("'", "''")


def sanitize_applescript_string(value: str) -> str:
    """
    Sanitizes a string for safe use in AppleScript quoted strings.
    Escapes backslashes and double quotes.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def validate_program_name(name: str) -> str:
    """
    Validates and sanitizes a program/service name.
    Only allows alphanumeric, spaces, hyphens, underscores, dots.

    Raises:
        ValueError: If name contains invalid characters
    """
    if not name or not name.strip():
        raise ValueError("Program name cannot be empty")

    # Allow only safe characters
    if not re.match(r'^[\w\s.\-()]+$', name):
        raise ValueError(
            f"Invalid program name: '{name}'. "
            "Only alphanumeric, spaces, hyphens, underscores, dots, and parentheses allowed."
        )

    return name.strip()


def validate_file_path(path: str) -> str:
    """
    Validates a file path for safe use in commands.
    Prevents path traversal and special character injection.

    Raises:
        ValueError: If path contains dangerous characters
    """
    if not path or not path.strip():
        raise ValueError("File path cannot be empty")

    # Block obvious injection attempts
    dangerous_patterns = [';', '|', '&', '`', '$', '\n', '\r']
    for pattern in dangerous_patterns:
        if pattern in path:
            raise ValueError(
                f"Invalid file path: contains dangerous character '{pattern}'"
            )

    return path.strip()


def validate_description(description: str, max_length: int = 200) -> str:
    """
    Validates a description string for safe use in commands.
    Strips dangerous characters and limits length.
    """
    if not description:
        return "TechCare"

    # Remove dangerous characters
    safe = re.sub(r'[;|&`$\n\r"\'\\]', '', description)

    return safe[:max_length].strip() or "TechCare"


def validate_integer(value, min_val: int = None, max_val: int = None) -> int:
    """
    Validates and converts a value to integer within bounds.

    Raises:
        ValueError: If value is not a valid integer or out of bounds
    """
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid integer value: {value}")

    if min_val is not None and result < min_val:
        raise ValueError(f"Value {result} below minimum {min_val}")
    if max_val is not None and result > max_val:
        raise ValueError(f"Value {result} above maximum {max_val}")

    return result
