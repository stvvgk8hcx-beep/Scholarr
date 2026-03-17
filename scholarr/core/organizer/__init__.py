"""File organization and naming service for academic files."""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ColonReplacementFormat(str, Enum):
    """Format options for replacing colons in filenames."""

    DASH = "-"
    UNDERSCORE = "_"
    SPACE = " "
    REMOVE = ""


@dataclass
class NamingContext:
    """Context containing all available tokens for filename/path building."""

    # Semester tokens
    semester: Optional[str] = None
    term: Optional[str] = None
    year: Optional[int] = None

    # Course tokens
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    course_section: Optional[str] = None
    professor: Optional[str] = None
    credits: Optional[float] = None

    # Item tokens
    item_type: Optional[str] = None
    item_number: Optional[str] = None
    item_topic: Optional[str] = None
    item_name: Optional[str] = None

    # Date tokens
    due_date: Optional[datetime] = None
    date_received: Optional[datetime] = None
    date_format: str = "%Y-%m-%d"

    # Grade/Status tokens
    grade: Optional[float] = None
    status: Optional[str] = None
    weight: Optional[float] = None

    # File tokens
    file_type: Optional[str] = None
    file_format: Optional[str] = None
    original_filename: Optional[str] = None
    extension: Optional[str] = None

    # File quality/version tokens
    file_quality: Optional[str] = None
    file_version: Optional[int] = None

    # Custom tokens
    custom_tokens: dict = field(default_factory=dict)


class FileNameBuilder:
    """Builder for creating standardized filenames and folder paths."""

    # All supported token patterns
    TOKENS = {
        # Semester tokens
        "Semester": ("semester",),
        "Term": ("term",),
        "Year": ("year",),
        # Course tokens
        "Course Code": ("course_code",),
        "Course Name": ("course_name",),
        "Course Section": ("course_section",),
        "Professor": ("professor",),
        "Credits": ("credits",),
        # Item tokens
        "Item Type": ("item_type",),
        "Item Number": ("item_number",),
        "Item Number:00": ("item_number",),  # zero-padded variant
        "Item Topic": ("item_topic",),
        "Item Name": ("item_name",),
        # Date tokens
        "Due Date": ("due_date",),
        "Date Received": ("date_received",),
        # Grade/Status tokens
        "Grade": ("grade",),
        "Status": ("status",),
        "Weight": ("weight",),
        # File tokens
        "File Type": ("file_type",),
        "File Format": ("file_format",),
        "Original Filename": ("original_filename",),
        "Extension": ("extension",),
        "ext": ("extension",),  # lowercase variant
        # File quality tokens
        "File Quality": ("file_quality",),
        "File Version": ("file_version",),
    }

    def __init__(self, colon_replacement: ColonReplacementFormat = ColonReplacementFormat.DASH):
        """Initialize the filename builder.

        Args:
            colon_replacement: Format to use when replacing colons in filenames.
        """
        self.colon_replacement = colon_replacement

    def build_filename(
        self,
        naming_format: str,
        context: NamingContext,
        date_format: str | None = None,
        colon_format: "ColonReplacementFormat | None" = None,
    ) -> str:
        """Build a filename from a format string and context.

        Args:
            naming_format: Format string with {Token} placeholders.
            context: NamingContext with token values.
            date_format: Optional override for the date format string (e.g. "%d-%b-%Y").
            colon_format: Optional override for colon replacement behaviour.

        Returns:
            str: The formatted filename with illegal characters cleaned.

        Raises:
            ValueError: If naming_format is invalid.
        """
        if not naming_format:
            raise ValueError("naming_format cannot be empty")

        # Apply date format override if provided
        if date_format:
            context = NamingContext(
                **{k: v for k, v in context.__dict__.items() if k != "date_format"},
                date_format=date_format,
            )

        # Temporarily override colon replacement
        original_colon = self.colon_replacement
        if colon_format is not None:
            self.colon_replacement = colon_format

        try:
            filename = naming_format
            tokens_used = self._extract_tokens(naming_format)

            for token in tokens_used:
                value = self._get_token_value(token, context)
                placeholder = "{" + token + "}"
                if value is not None:
                    # Format the value appropriately
                    formatted_value = self._format_value(token, value, context)
                    filename = filename.replace(placeholder, str(formatted_value))
                else:
                    # Remove the placeholder and any adjacent separator
                    filename = re.sub(
                        r"(?:[_\-]?" + re.escape(placeholder) + r"[_\-]?)",
                        "_",
                        filename,
                    )

            # Clean up any remaining unreplaced tokens
            filename = re.sub(r"\{[^}]+\}", "", filename)

            # Remove consecutive separators and trailing/leading underscores/dashes
            filename = re.sub(r"[_\-]{2,}", "_", filename)
            filename = filename.strip("_-")

            # Clean illegal characters
            filename = self.clean_filename(filename)
        finally:
            self.colon_replacement = original_colon

        return filename

    def build_path(self, path_format: str, context: NamingContext) -> str:
        """Alias for build_folder_path."""
        return self.build_folder_path(path_format, context)

    def build_folder_path(self, path_format: str, context: NamingContext) -> str:
        """Build a folder path from a format string and context.

        Args:
            path_format: Format string with {Token} placeholders and / separators.
            context: NamingContext with token values.

        Returns:
            str: The formatted folder path.

        Raises:
            ValueError: If path_format is invalid.
        """
        if not path_format:
            raise ValueError("path_format cannot be empty")

        parts = path_format.split("/")
        built_parts = []

        for part in parts:
            built_part = self.build_filename(part, context)
            if built_part:  # Skip empty parts
                built_parts.append(built_part)

        return "/".join(built_parts)

    def _extract_tokens(self, text: str) -> list[str]:
        """Extract all token placeholders from text.

        Args:
            text: Text potentially containing {Token} placeholders.

        Returns:
            list[str]: List of token names found.
        """
        pattern = r"\{([^}]+)\}"
        return re.findall(pattern, text)

    def _get_token_value(self, token: str, context: NamingContext):
        """Get the value for a token from context.

        Args:
            token: Token name (e.g., "Course Code").
            context: NamingContext with values.

        Returns:
            Value for the token, or None if not available.
        """
        import re as _re

        # Check custom tokens first
        if token in context.custom_tokens:
            return context.custom_tokens[token]

        # Handle arbitrary zero-padding variants: "Item Number:000", "Item Number:0000", etc.
        if _re.match(r"^Item Number:0+$", token, _re.IGNORECASE):
            return context.item_number

        # Check standard tokens (case-insensitive lookup)
        for key, field_names in self.TOKENS.items():
            if key.lower() == token.lower() or token.lower() == key.lower().replace(" ", ""):
                field_name = field_names[0]
                return getattr(context, field_name, None)

        return None

    def _format_value(self, token: str, value, context: NamingContext) -> str:
        """Format a value based on token type.

        Args:
            token: Token name.
            value: Raw value to format.
            context: NamingContext for reference.

        Returns:
            str: Formatted value.
        """
        # Handle date formatting
        if token in ("Due Date", "Date Received"):
            if isinstance(value, datetime):
                return value.strftime(context.date_format)
            return str(value)

        # Handle zero-padded item number: "Item Number:00", "Item Number:000", etc.
        import re as _re
        if _re.match(r"^Item Number:0+$", token, _re.IGNORECASE):
            zero_count = len(token.split(":")[-1])
            try:
                if "." in str(value):
                    num = int(float(str(value).split(".")[0]))
                else:
                    num = int(str(value))
                return str(num).zfill(zero_count)
            except (ValueError, IndexError):
                return str(value)

        # Handle numeric values
        if isinstance(value, (int, float)):
            return str(value)

        return str(value)

    def clean_filename(self, filename: str, colon_replacement: Optional[ColonReplacementFormat] = None) -> str:
        """Clean illegal characters from a filename.

        Args:
            filename: Filename to clean.
            colon_replacement: Format for replacing colons. Uses default if not provided.

        Returns:
            str: Cleaned filename.
        """
        if not filename:
            return filename

        replacement = colon_replacement or self.colon_replacement

        # Replace colons
        if replacement == ColonReplacementFormat.REMOVE:
            filename = filename.replace(":", "")
        else:
            filename = filename.replace(":", replacement.value)

        # Remove or replace other illegal characters
        # These are illegal on Windows, Mac, and Linux
        illegal_chars = r'[<>"|?*\x00-\x1f]'
        filename = re.sub(illegal_chars, "", filename)

        # Replace multiple spaces with single space
        filename = re.sub(r"\s+", " ", filename)

        # Remove leading/trailing whitespace
        filename = filename.strip()

        # Remove leading/trailing dots and spaces (problematic on Windows)
        filename = filename.rstrip(". ")

        # Ensure filename is not empty
        if not filename:
            filename = "file"

        return filename

    def validate_format_string(self, format_string: str) -> tuple[bool, list[str]]:
        """Validate a format string for proper token syntax.

        Args:
            format_string: Format string to validate.

        Returns:
            tuple: (is_valid, list_of_invalid_tokens)
        """
        if not format_string:
            return False, ["Format string cannot be empty"]

        invalid_tokens = []
        tokens = self._extract_tokens(format_string)

        for token in tokens:
            # Check if it's a valid token or custom token placeholder
            is_valid = False

            # Allow arbitrary zero-padding variants of Item Number
            if re.match(r"^Item Number:0+$", token, re.IGNORECASE):
                is_valid = True

            if not is_valid:
                # Check against known tokens
                for key in self.TOKENS.keys():
                    if key.lower() == token.lower() or token.lower() == key.lower().replace(" ", ""):
                        is_valid = True
                        break

            # Allow custom tokens (they'll be resolved from context)
            if not is_valid and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", token):
                is_valid = True

            if not is_valid:
                invalid_tokens.append(token)

        return len(invalid_tokens) == 0, invalid_tokens

    def get_supported_tokens(self) -> list[str]:
        """Get list of all supported tokens.

        Returns:
            list[str]: All supported token names.
        """
        return list(self.TOKENS.keys())
