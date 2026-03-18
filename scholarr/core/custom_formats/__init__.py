"""Custom file format specifications and service."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.exceptions import NotFoundError, ValidationException

logger = logging.getLogger(__name__)


@dataclass
class FormatSpecification:
    """Specification for a custom file format."""

    extensions: list[str]
    min_size: int | None = None
    max_size: int | None = None
    filename_regex: str | None = None

    def to_dict(self) -> dict:
        """Convert specification to dictionary.

        Returns:
            dict: Dictionary representation of specification.
        """
        return {
            "extensions": self.extensions,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "filename_regex": self.filename_regex,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormatSpecification":
        """Create specification from dictionary.

        Args:
            data: Dictionary with specification data.

        Returns:
            FormatSpecification: New specification instance.

        Raises:
            ValidationException: If data is invalid.
        """
        try:
            return cls(
                extensions=data.get("extensions", []),
                min_size=data.get("min_size"),
                max_size=data.get("max_size"),
                filename_regex=data.get("filename_regex"),
            )
        except (KeyError, TypeError) as e:
            raise ValidationException(f"Invalid format specification: {e}") from e


class CustomFormatService:
    """Service for managing custom file format specifications."""

    def __init__(self, session: AsyncSession):
        """Initialize custom format service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_all(self) -> list:
        """Get all custom formats.

        Returns:
            list: List of custom format records.
        """
        from scholarr.db.models import CustomFormat

        result = await self.session.execute(select(CustomFormat))
        return list(result.scalars().all())

    async def get_by_id(self, format_id: int):
        """Get custom format by ID.

        Args:
            format_id: Format ID.

        Returns:
            CustomFormat: The custom format record.

        Raises:
            NotFoundError: If format not found.
        """
        from scholarr.db.models import CustomFormat

        result = await self.session.execute(select(CustomFormat).where(CustomFormat.id == format_id))
        custom_format = result.scalar_one_or_none()

        if not custom_format:
            raise NotFoundError(f"Custom format {format_id} not found")

        return custom_format

    async def get_by_name(self, name: str):
        """Get custom format by name.

        Args:
            name: Format name.

        Returns:
            CustomFormat: The custom format record.

        Raises:
            NotFoundError: If format not found.
        """
        from scholarr.db.models import CustomFormat

        result = await self.session.execute(select(CustomFormat).where(CustomFormat.name == name))
        custom_format = result.scalar_one_or_none()

        if not custom_format:
            raise NotFoundError(f"Custom format '{name}' not found")

        return custom_format

    async def create(self, name: str, specifications: dict, include_when_renaming: bool = True) -> object:
        """Create a new custom format.

        Args:
            name: Format name.
            specifications: Format specifications dictionary.
            include_when_renaming: Whether to include in renaming operations.

        Returns:
            CustomFormat: The created custom format.

        Raises:
            ValidationException: If data is invalid.
        """
        from scholarr.db.models import CustomFormat

        # Validate specification
        try:
            FormatSpecification.from_dict(specifications)
        except ValidationException as e:
            raise ValidationException(f"Invalid format specification: {e}") from e

        custom_format = CustomFormat(
            name=name,
            specifications=specifications,
            include_when_renaming=include_when_renaming,
        )
        self.session.add(custom_format)
        await self.session.commit()
        await self.session.refresh(custom_format)

        return custom_format

    async def update(self, format_id: int, data: dict):
        """Update a custom format.

        Args:
            format_id: Format ID.
            data: Fields to update.

        Returns:
            CustomFormat: The updated custom format.

        Raises:
            NotFoundError: If format not found.
            ValidationException: If data is invalid.
        """
        custom_format = await self.get_by_id(format_id)

        # Validate specifications if being updated
        if "specifications" in data:
            try:
                FormatSpecification.from_dict(data["specifications"])
            except ValidationException as e:
                raise ValidationException(f"Invalid format specification: {e}") from e

        for key, value in data.items():
            if hasattr(custom_format, key):
                setattr(custom_format, key, value)

        self.session.add(custom_format)
        await self.session.commit()
        await self.session.refresh(custom_format)

        return custom_format

    async def delete(self, format_id: int):
        """Delete a custom format.

        Args:
            format_id: Format ID.

        Raises:
            NotFoundError: If format not found.
        """
        custom_format = await self.get_by_id(format_id)
        await self.session.delete(custom_format)
        await self.session.commit()

    def match_file(self, file_path: str | Path, format_spec: dict) -> bool:
        """Check if a file matches a custom format specification.

        Args:
            file_path: Path to the file to check.
            format_spec: Format specification dictionary.

        Returns:
            bool: True if file matches the format specification.
        """
        try:
            spec = FormatSpecification.from_dict(format_spec)
        except ValidationException:
            logger.warning("Invalid format specification provided to match_file")
            return False

        file_path = Path(file_path)

        # Check extension
        file_ext = file_path.suffix.lstrip(".").lower()
        if spec.extensions:
            extensions_lower = [ext.lower() for ext in spec.extensions]
            if file_ext not in extensions_lower:
                return False

        # Check file size
        try:
            file_size = file_path.stat().st_size
            if spec.min_size is not None and file_size < spec.min_size:
                return False
            if spec.max_size is not None and file_size > spec.max_size:
                return False
        except (OSError, ValueError):
            logger.warning(f"Could not determine file size for {file_path}")
            return False

        # Check filename regex
        if spec.filename_regex:
            try:
                pattern = re.compile(spec.filename_regex, re.IGNORECASE)
                if not pattern.search(file_path.name):
                    return False
            except re.error as e:
                logger.warning(f"Invalid regex pattern in format specification: {e}")
                return False

        return True

    async def find_matching_formats(self, file_path: str) -> list:
        """Find all custom formats that match a file.

        Args:
            file_path: Path to the file.

        Returns:
            list: List of matching CustomFormat records.
        """
        all_formats = await self.get_all()
        matching = []

        for fmt in all_formats:
            if self.match_file(file_path, fmt.specifications):
                matching.append(fmt)

        return matching
