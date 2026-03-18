"""Decision engine for evaluating file imports."""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.parser import ParseResult

logger = logging.getLogger(__name__)


class ImportAction(str, Enum):
    """Actions that can be taken for an import decision."""

    ACCEPT = "Accept"
    REJECT = "Reject"
    UPGRADE = "Upgrade"
    SKIP = "Skip"


class QualityRank(str, Enum):
    """File quality rankings based on format."""

    HIGHEST = "PDF"
    HIGH = "DOCX"
    MEDIUM = "XLSX"
    LOW = "TXT"
    LOWEST = "OTHER"


@dataclass
class DecisionResult:
    """Result of a file import decision."""

    action: ImportAction
    reason: str
    existing_file_id: int | None = None
    quality_score: float = 0.0


class DecisionEngine:
    """Engine for making import decisions based on file characteristics and rules."""

    # File format quality rankings
    FORMAT_QUALITY = {
        "pdf": QualityRank.HIGHEST,
        "docx": QualityRank.HIGH,
        "doc": QualityRank.HIGH,
        "xlsx": QualityRank.MEDIUM,
        "xls": QualityRank.MEDIUM,
        "csv": QualityRank.MEDIUM,
        "txt": QualityRank.LOW,
        "rtf": QualityRank.LOW,
    }

    # Size limits (in bytes)
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
    MIN_FILE_SIZE = 1  # 1 byte

    def __init__(self, session: AsyncSession):
        """Initialize the decision engine.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def evaluate(
        self, file_path: str | Path, parse_result: ParseResult, course_id: int
    ) -> DecisionResult:
        """Evaluate a file and make an import decision.

        Args:
            file_path: Path to the file being imported.
            parse_result: Parsed filename metadata.
            course_id: ID of the course to import into.

        Returns:
            DecisionResult: Decision on how to handle the file.
        """
        file_path = Path(file_path)

        # Step 1: Check if file exists and is readable
        if not file_path.exists():
            return DecisionResult(
                action=ImportAction.REJECT, reason=f"File does not exist: {file_path}"
            )

        if not file_path.is_file():
            return DecisionResult(
                action=ImportAction.REJECT, reason=f"Path is not a file: {file_path}"
            )

        # Step 2: Check file size
        try:
            file_size = file_path.stat().st_size
        except OSError as e:
            return DecisionResult(
                action=ImportAction.REJECT, reason=f"Cannot access file: {e}"
            )

        if file_size < self.MIN_FILE_SIZE:
            return DecisionResult(
                action=ImportAction.REJECT,
                reason=f"File is empty or too small ({file_size} bytes)",
            )

        if file_size > self.MAX_FILE_SIZE:
            return DecisionResult(
                action=ImportAction.REJECT,
                reason=f"File exceeds maximum size ({file_size} > {self.MAX_FILE_SIZE} bytes)",
            )

        # Step 3: Check file extension
        file_ext = file_path.suffix.lstrip(".").lower()
        quality_score = self._calculate_quality_score(file_ext)

        if quality_score == 0:
            return DecisionResult(
                action=ImportAction.REJECT,
                reason=f"Unsupported file format: .{file_ext}",
                quality_score=quality_score,
            )

        # Step 4: Calculate file hash and check for duplicates
        from scholarr.core.managed_files import ManagedFileService

        try:
            file_hash = await self._calculate_file_hash(file_path)
        except OSError as e:
            return DecisionResult(
                action=ImportAction.REJECT, reason=f"Cannot read file for hashing: {e}"
            )

        managed_file_service = ManagedFileService(self.session)
        existing_file = await managed_file_service.get_by_hash(file_hash)

        if existing_file:
            # File with same content already exists
            existing_quality = self._calculate_quality_score(
                existing_file.format or "other"
            )

            if quality_score > existing_quality:
                # New file is higher quality, allow upgrade
                return DecisionResult(
                    action=ImportAction.UPGRADE,
                    reason=f"New file is higher quality ({quality_score:.1f} > {existing_quality:.1f})",
                    existing_file_id=existing_file.id,
                    quality_score=quality_score,
                )
            else:
                # Existing file is same or better quality, skip
                return DecisionResult(
                    action=ImportAction.SKIP,
                    reason="File with same content already exists and is same or better quality",
                    existing_file_id=existing_file.id,
                    quality_score=quality_score,
                )

        # Step 5: Check file profile constraints
        course = await self._get_course(course_id)
        if not course:
            return DecisionResult(
                action=ImportAction.REJECT, reason=f"Course {course_id} not found"
            )

        # Check against file profile if set
        if hasattr(course, "file_profile") and course.file_profile:
            profile_check = await self._check_profile_compatibility(file_ext, course)
            if not profile_check:
                return DecisionResult(
                    action=ImportAction.REJECT,
                    reason=f"File format .{file_ext} not allowed by course file profile",
                    quality_score=quality_score,
                )

        # Step 6: All checks passed
        return DecisionResult(
            action=ImportAction.ACCEPT,
            reason="File passed all validation checks",
            quality_score=quality_score,
        )

    def _calculate_quality_score(self, file_ext: str) -> float:
        """Calculate quality score based on file format.

        Args:
            file_ext: File extension (without dot).

        Returns:
            float: Quality score (0.0 to 1.0).
        """
        ext = file_ext.lower().strip()
        quality_map = {
            QualityRank.HIGHEST: 1.0,
            QualityRank.HIGH: 0.8,
            QualityRank.MEDIUM: 0.6,
            QualityRank.LOW: 0.4,
            QualityRank.LOWEST: 0.0,
        }

        rank = self.FORMAT_QUALITY.get(ext, QualityRank.LOWEST)
        return quality_map.get(rank, 0.0)

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content.

        Args:
            file_path: Path to the file.

        Returns:
            str: Hex-encoded SHA256 hash.
        """
        import hashlib

        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def _get_course(self, course_id: int):
        """Get course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course: The course record or None.
        """
        from scholarr.db.models import Course

        result = await self.session.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def _check_profile_compatibility(self, file_ext: str, course) -> bool:
        """Check if file format is compatible with course's file profile.

        Args:
            file_ext: File extension.
            course: Course record.

        Returns:
            bool: True if compatible.
        """
        if not hasattr(course, "file_profile"):
            return True

        profile = course.file_profile
        if not profile:
            return True

        # Check if extension is in allowed formats
        if hasattr(profile, "allowed_formats"):
            for fmt in profile.allowed_formats:
                if hasattr(fmt, "specifications"):
                    extensions = fmt.specifications.get("extensions", [])
                    if file_ext.lower() in [e.lower() for e in extensions]:
                        return True
            return len(profile.allowed_formats) > 0

        return True

    async def should_upgrade(
        self, new_file_quality: float, existing_file_id: int
    ) -> bool:
        """Determine if a file should be upgraded.

        Args:
            new_file_quality: Quality score of new file.
            existing_file_id: ID of existing file.

        Returns:
            bool: True if upgrade should proceed.
        """
        from scholarr.core.managed_files import ManagedFileService

        managed_file_service = ManagedFileService(self.session)

        try:
            existing_file = await managed_file_service.get_by_id(existing_file_id)
            existing_quality = self._calculate_quality_score(existing_file.format or "other")
            return new_file_quality > existing_quality
        except Exception as e:
            logger.warning(f"Error checking upgrade eligibility: {e}")
            return False

    def get_quality_ranking(self, file_ext: str) -> QualityRank | None:
        """Get quality rank for a file extension.

        Args:
            file_ext: File extension.

        Returns:
            QualityRank: The quality rank, or None if unknown.
        """
        return self.FORMAT_QUALITY.get(file_ext.lower().strip())

    def get_supported_formats(self) -> list[str]:
        """Get list of supported file formats.

        Returns:
            list[str]: Supported file extensions.
        """
        return list(self.FORMAT_QUALITY.keys())
