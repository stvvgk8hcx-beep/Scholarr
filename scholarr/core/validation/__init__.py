"""Data validation utilities for Scholarr."""

import os
import re
from typing import Optional

from scholarr.core.exceptions import ValidationException as ValidationError


def validate_path(path: str) -> bool:
    """Validate that a path doesn't contain directory traversal attacks.

    Args:
        path: Path to validate.

    Returns:
        bool: True if path is valid.

    Raises:
        ValidationError: If path contains traversal sequences.
    """
    if ".." in path or path.startswith("/"):
        raise ValidationError("Path contains invalid traversal sequence")

    normalized = os.path.normpath(path)
    if normalized.startswith(".."):
        raise ValidationError("Path attempts to escape base directory")

    return True


def validate_course_code(code: str) -> bool:
    """Validate course code format.

    Args:
        code: Course code to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValidationError: If format is invalid.
    """
    if not code or not 2 <= len(code) <= 10:
        raise ValidationError("Course code must be 2-10 characters")

    if not re.match(r"^[A-Z0-9\s\-]+$", code, re.IGNORECASE):
        raise ValidationError("Course code contains invalid characters")

    return True


def validate_grade(grade: str) -> bool:
    """Validate grade format (letter or percentage).

    Args:
        grade: Grade to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValidationError: If format is invalid.
    """
    grade_upper = grade.upper().strip()

    letter_pattern = r"^[A-F][+-]?$"
    if re.match(letter_pattern, grade_upper):
        return True

    try:
        percent = float(grade)
        if 0 <= percent <= 100:
            return True
    except ValueError:
        pass

    raise ValidationError("Grade must be a letter grade (A-F) or percentage (0-100)")


def validate_file_extension(
    extension: str,
    allowed: Optional[list[str]] = None,
    blocked: Optional[list[str]] = None,
) -> bool:
    """Validate file extension.

    Args:
        extension: File extension to validate.
        allowed: List of allowed extensions (without dots).

    Returns:
        bool: True if valid.

    Raises:
        ValidationError: If extension is not allowed.
    """
    ext = extension.lstrip(".")

    if not ext:
        raise ValidationError("File extension cannot be empty")

    if len(ext) > 10:
        raise ValidationError("File extension too long")

    if not re.match(r"^[a-z0-9]+$", ext, re.IGNORECASE):
        raise ValidationError("File extension contains invalid characters")

    if blocked and ext.lower() in [b.lower() for b in blocked]:
        raise ValidationError(f"File extension .{ext} is not permitted")

    if allowed:
        if ext.lower() not in [a.lower() for a in allowed]:
            raise ValidationError(
                f"File extension .{ext} not allowed. Allowed: {', '.join(allowed)}"
            )

    return True


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValidationError: If format is invalid.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValidationError("Invalid email address format")

    return True


def validate_semester_dates(start_date, end_date) -> bool:
    """Validate that semester end date is after start date.

    Args:
        start_date: Semester start date.
        end_date: Semester end date.

    Returns:
        bool: True if valid.

    Raises:
        ValidationError: If dates are invalid.
    """
    if end_date <= start_date:
        raise ValidationError("End date must be after start date")

    return True


def validate_string_length(
    value: str,
    min_length: int = 1,
    max_length: int = 255,
) -> bool:
    """Validate string length.

    Args:
        value: String to validate.
        min_length: Minimum length.
        max_length: Maximum length.

    Returns:
        bool: True if valid.

    Raises:
        ValidationError: If length is invalid.
    """
    if not value or len(value) < min_length:
        raise ValidationError(f"String must be at least {min_length} characters")

    if len(value) > max_length:
        raise ValidationError(f"String must be at most {max_length} characters")

    return True
