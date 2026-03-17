"""File name parser for extracting metadata from academic file names."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ItemType(str, Enum):
    """Types of academic items that can be parsed."""

    ASSIGNMENT = "Assignment"
    LAB = "Lab"
    LECTURE = "Lecture"
    EXAM = "Exam"
    PAPER = "Paper"
    PROJECT = "Project"
    NOTES = "Notes"
    SYLLABUS = "Syllabus"
    TEXTBOOK = "Textbook"
    SLIDES = "Slides"
    TUTORIAL = "Tutorial"
    QUIZ = "Quiz"
    OTHER = "Other"


@dataclass
class ParseResult:
    """Result of parsing a filename."""

    course_code: Optional[str] = None
    item_type: Optional[ItemType] = None
    item_number: Optional[str] = None
    topic: Optional[str] = None
    version: Optional[str] = None
    date_hint: Optional[str] = None
    confidence_score: float = 0.0


class FileNameParser:
    """Parser for extracting metadata from academic filenames."""

    # Item type keywords mapped to ItemType enum
    ITEM_TYPE_KEYWORDS = {
        "assignment": ItemType.ASSIGNMENT,
        "assign": ItemType.ASSIGNMENT,
        "hw": ItemType.ASSIGNMENT,
        "homework": ItemType.ASSIGNMENT,
        "lab": ItemType.LAB,
        "practical": ItemType.LAB,
        "lecture": ItemType.LECTURE,
        "lec": ItemType.LECTURE,
        "exam": ItemType.EXAM,
        "test": ItemType.EXAM,
        "midterm": ItemType.EXAM,
        "final": ItemType.EXAM,
        "paper": ItemType.PAPER,
        "essay": ItemType.PAPER,
        "project": ItemType.PROJECT,
        "notes": ItemType.NOTES,
        "note": ItemType.NOTES,
        "syllabus": ItemType.SYLLABUS,
        "textbook": ItemType.TEXTBOOK,
        "slides": ItemType.SLIDES,
        "slide": ItemType.SLIDES,
        "tutorial": ItemType.TUTORIAL,
        "tut": ItemType.TUTORIAL,
        "quiz": ItemType.QUIZ,
    }

    # Version hint keywords
    VERSION_KEYWORDS = {"draft", "final", "graded", "v2", "v1", "version", "rev", "revision"}

    def __init__(self):
        """Initialize the parser with regex patterns."""
        # Pattern for course codes (e.g., "BCS310", "MAT235", "CS101")
        self.course_code_pattern = re.compile(r"([A-Z]{2,4}\d{2,4})", re.IGNORECASE)

        # Pattern for item number (e.g., "3", "3.5", "#3")
        self.item_number_pattern = re.compile(r"#?(\d+(?:\.\d+)?)", re.IGNORECASE)

        # Pattern for item type in various formats
        self.item_type_pattern = self._build_item_type_pattern()

        # Pattern for version hints — use lookahead/lookbehind instead of \b so
        # that underscore-separated tokens (e.g. "Assignment3_draft") still match.
        self.version_pattern = re.compile(
            r"(?<![a-zA-Z0-9])(draft|final|graded|v\d+|version|rev\d*|revision)(?![a-zA-Z0-9])",
            re.IGNORECASE,
        )

        # Pattern for date hints (basic ISO date format and variations)
        self.date_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})", re.IGNORECASE
        )

    def _build_item_type_pattern(self) -> re.Pattern:
        """Build regex pattern for item type keywords.

        Uses a lookahead so that keywords immediately followed by a digit or
        non-alpha char are still matched (e.g. "Lab3", "CSCLab1", "MAT235Exam").
        Does NOT use a leading \\b so it matches after a course-code prefix too.
        """
        keywords = "|".join(self.ITEM_TYPE_KEYWORDS.keys())
        # Require digit, non-word char, or end-of-string after the keyword so that
        # "lab" in "laboratory" doesn't false-match, but "Lab3" and "CSCLab1" do.
        return re.compile(rf"({keywords})(?=\d|\W|$)", re.IGNORECASE)

    def parse(self, filename: str) -> ParseResult:
        """Parse a filename and extract academic metadata.

        Args:
            filename: The filename to parse (without path).

        Returns:
            ParseResult: Extracted metadata with confidence score.
        """
        result = ParseResult()
        confidence = 0.0
        max_confidence = 0.0

        # Remove extension for cleaner parsing
        name_without_ext = self._remove_extension(filename)

        # Try different parsing strategies
        results = [
            self._parse_standard_format(name_without_ext),
            self._parse_underscore_format(name_without_ext),
            self._parse_dash_format(name_without_ext),
            self._parse_space_format(name_without_ext),
        ]

        # Use the result with highest confidence
        for res in results:
            if res.confidence_score > max_confidence:
                max_confidence = res.confidence_score
                result = res

        # Always try to extract course code, version, and date even if not found in specific format
        if not result.course_code:
            result.course_code = self._extract_course_code(name_without_ext)
            if result.course_code:
                confidence += 0.1

        if not result.version:
            result.version = self._extract_version(name_without_ext)
            if result.version:
                confidence += 0.05

        if not result.date_hint:
            result.date_hint = self._extract_date(name_without_ext)
            if result.date_hint:
                confidence += 0.05

        result.confidence_score = min(1.0, max_confidence + confidence)
        return result

    def _remove_extension(self, filename: str) -> str:
        """Remove file extension from filename."""
        return re.sub(r"\.\w+$", "", filename)

    def _extract_course_code(self, text: str) -> Optional[str]:
        """Extract course code (e.g., BCS310, MAT235).

        Filters out matches whose letter prefix is a known item-type keyword
        (e.g., LAB03, EXAM2) since those are item descriptors, not course codes.
        """
        match = self.course_code_pattern.search(text)
        if not match:
            return None
        code = match.group(1).upper()
        # Extract the letter prefix and reject if it's an item-type keyword
        prefix = "".join(ch for ch in code if ch.isalpha()).lower()
        if prefix in self.ITEM_TYPE_KEYWORDS:
            return None
        return code

    def _extract_item_number(self, text: str) -> Optional[str]:
        """Extract item number (e.g., 3, 3.5)."""
        # Look for patterns like "Lab3", "Assignment 3", "#3"
        match = self.item_number_pattern.search(text)
        return match.group(1) if match else None

    def _extract_item_type(self, text: str) -> Optional[ItemType]:
        """Extract item type from text."""
        match = self.item_type_pattern.search(text)
        if match:
            keyword = match.group(1).lower()
            return self.ITEM_TYPE_KEYWORDS.get(keyword)
        return None

    def _extract_version(self, text: str) -> Optional[str]:
        """Extract version hint from text."""
        match = self.version_pattern.search(text)
        return match.group(1).lower() if match else None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date hint from text."""
        match = self.date_pattern.search(text)
        return match.group(1) if match else None

    def _extract_topic(self, text: str, item_type: Optional[ItemType] = None) -> Optional[str]:
        """Extract topic/description from text."""
        # Remove common elements to get cleaner topic
        topic = text
        topic = re.sub(r"\b(draft|final|graded|v\d+|version)\b", "", topic, flags=re.IGNORECASE)
        topic = re.sub(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}", "", topic)
        topic = topic.strip()

        # Remove item type if present
        if item_type:
            topic = re.sub(rf"\b{item_type.value}\b", "", topic, flags=re.IGNORECASE).strip()

        # Clean up separators
        topic = re.sub(r"[-_\s]+", " ", topic).strip()

        return topic if topic else None

    def _parse_standard_format(self, filename: str) -> ParseResult:
        """Parse standard format: CourseCode_ItemType#_Topic_Version.

        Example: BCS310_Lab3_BinarySearchTrees_Final.pdf
        """
        result = ParseResult()
        confidence = 0.0

        parts = re.split(r"[_\-]", filename)
        if len(parts) >= 2:
            course_code_part_idx: int | None = None

            # Try to find course code in first parts
            for i, part in enumerate(parts):
                course_code = self._extract_course_code(part)
                if course_code:
                    result.course_code = course_code
                    course_code_part_idx = i
                    confidence += 0.3
                    break

            # Look for item type
            for part in parts:
                item_type = self._extract_item_type(part)
                if item_type:
                    result.item_type = item_type
                    confidence += 0.2
                    break

            # Look for item number — skip the part that contains the course code
            for i, part in enumerate(parts):
                if i == course_code_part_idx:
                    continue
                item_num = self._extract_item_number(part)
                if item_num:
                    result.item_number = item_num
                    confidence += 0.1
                    break

            # Look for version hints
            for part in parts:
                version = self._extract_version(part)
                if version:
                    result.version = version
                    confidence += 0.1
                    break

            # Combine remaining parts as topic
            topic_parts = [
                p
                for p in parts
                if not self._extract_course_code(p)
                and not self._extract_item_type(p)
                and not self._extract_version(p)
                and not self._extract_item_number(p)
            ]
            if topic_parts:
                result.topic = " ".join(topic_parts)
                confidence += 0.15

        result.confidence_score = confidence
        return result

    def _parse_underscore_format(self, filename: str) -> ParseResult:
        """Parse underscore-separated format.

        Example: Lecture_Notes_Week5.pdf
        """
        result = ParseResult()
        confidence = 0.0

        if "_" in filename:
            parts = filename.split("_")

            # First part might be item type
            item_type = self._extract_item_type(parts[0])
            if item_type:
                result.item_type = item_type
                confidence += 0.2

            # Look through all parts
            for part in parts:
                if not result.course_code:
                    course_code = self._extract_course_code(part)
                    if course_code:
                        result.course_code = course_code
                        confidence += 0.15

                if not result.item_number:
                    item_num = self._extract_item_number(part)
                    if item_num:
                        result.item_number = item_num
                        confidence += 0.1

            # Remaining text is likely topic
            remaining = re.sub(
                r"\b(draft|final|graded|v\d+)\b", "", filename, flags=re.IGNORECASE
            ).strip()
            if remaining:
                result.topic = remaining
                confidence += 0.1

        result.confidence_score = confidence
        return result

    def _parse_dash_format(self, filename: str) -> ParseResult:
        """Parse dash-separated format.

        Example: lab03-binary-search.py
        """
        result = ParseResult()
        confidence = 0.0

        if "-" in filename:
            parts = filename.split("-")

            # Look for item type in first part
            for part in parts:
                item_type = self._extract_item_type(part)
                if item_type:
                    result.item_type = item_type
                    confidence += 0.2
                    break

            # Look for item number in first or second part
            for part in parts[:3]:
                item_num = self._extract_item_number(part)
                if item_num:
                    result.item_number = item_num
                    confidence += 0.15
                    break

            # Remaining parts form topic
            topic_parts = [
                p
                for p in parts
                if not self._extract_item_type(p) and not self._extract_item_number(p)
            ]
            if topic_parts:
                result.topic = "-".join(topic_parts)
                confidence += 0.1

        result.confidence_score = confidence
        return result

    def _parse_space_format(self, filename: str) -> ParseResult:
        """Parse space-separated format.

        Example: Assignment 3 - Data Structures
        """
        result = ParseResult()
        confidence = 0.0

        parts = filename.split()

        # Search all parts for item type (not just first word)
        for part in parts:
            if not result.item_type:
                item_type = self._extract_item_type(part)
                if item_type:
                    result.item_type = item_type
                    confidence += 0.2

        # Look through parts for course code and number, skipping course-code part
        course_code_part: str | None = None
        for part in parts:
            if not result.course_code:
                course_code = self._extract_course_code(part)
                if course_code:
                    result.course_code = course_code
                    course_code_part = part
                    confidence += 0.15

        for part in parts:
            if part == course_code_part:
                continue
            if not result.item_number:
                item_num = self._extract_item_number(part)
                if item_num:
                    result.item_number = item_num
                    confidence += 0.15

        # Get topic by removing item type and number
        topic_text = filename
        if result.item_type:
            topic_text = re.sub(rf"\b{result.item_type.value}\b", "", topic_text, flags=re.IGNORECASE)
        if result.item_number:
            topic_text = re.sub(rf"\b{result.item_number}\b", "", topic_text)
        topic_text = re.sub(r"[-–—]", " ", topic_text).strip()
        topic_text = re.sub(r"\s+", " ", topic_text).strip()

        if topic_text:
            result.topic = topic_text
            confidence += 0.1

        result.confidence_score = confidence
        return result
