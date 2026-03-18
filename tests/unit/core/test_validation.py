"""Unit tests for validation utilities."""

import pytest

from scholarr.core.exceptions import ValidationError
from scholarr.core.validation import (
    validate_course_code,
    validate_file_extension,
    validate_grade,
    validate_path,
)


class TestValidatePath:
    """Tests for path validation."""

    def test_validate_safe_path(self):
        """Test validating a safe path."""
        assert validate_path("data/files/course.pdf") is True

    def test_validate_path_with_subdirs(self):
        """Test validating path with multiple subdirectories."""
        assert validate_path("library/2024/fall/bcs310/assignment.pdf") is True

    def test_reject_path_traversal_parent(self):
        """Test rejecting path with parent directory traversal."""
        with pytest.raises(ValidationError):
            validate_path("../../../etc/passwd")

    def test_reject_path_traversal_double_dot(self):
        """Test rejecting path with .. traversal."""
        with pytest.raises(ValidationError):
            validate_path("files/../../../sensitive")

    def test_reject_absolute_path(self):
        """Test rejecting absolute paths."""
        with pytest.raises(ValidationError):
            validate_path("/etc/passwd")

    def test_reject_root_slash(self):
        """Test rejecting paths starting with /."""
        with pytest.raises(ValidationError):
            validate_path("/home/user/file.pdf")


class TestValidateCourseCode:
    """Tests for course code validation."""

    def test_validate_course_code_valid(self):
        """Test validating a valid course code."""
        assert validate_course_code("BCS310") is True

    def test_validate_course_code_with_space(self):
        """Test validating course code with space."""
        assert validate_course_code("CS 101") is True

    def test_validate_course_code_with_dash(self):
        """Test validating course code with dash."""
        assert validate_course_code("MAT-235") is True

    def test_reject_invalid_code_empty(self):
        """Test rejecting empty course code."""
        with pytest.raises(ValidationError):
            validate_course_code("")

    def test_reject_invalid_code_too_short(self):
        """Test rejecting course code that's too short."""
        with pytest.raises(ValidationError):
            validate_course_code("A")

    def test_reject_invalid_code_too_long(self):
        """Test rejecting course code that's too long."""
        with pytest.raises(ValidationError):
            validate_course_code("ABCD123456789")

    def test_reject_invalid_code_special_chars(self):
        """Test rejecting course code with invalid special characters."""
        with pytest.raises(ValidationError):
            validate_course_code("BCS@310")

    def test_validate_code_uppercase(self):
        """Test that codes are validated case-insensitively."""
        assert validate_course_code("bcs310") is True

    def test_validate_code_numeric(self):
        """Test numeric-only course codes."""
        assert validate_course_code("101") is True


class TestValidateGrade:
    """Tests for grade validation."""

    def test_validate_letter_grade_a(self):
        """Test validating letter grade A."""
        assert validate_grade("A") is True

    def test_validate_letter_grade_with_plus(self):
        """Test validating letter grade with plus."""
        assert validate_grade("A+") is True

    def test_validate_letter_grade_with_minus(self):
        """Test validating letter grade with minus."""
        assert validate_grade("B-") is True

    def test_validate_all_letter_grades(self):
        """Test all valid letter grades."""
        grades = ["A", "B", "C", "D", "F"]
        for grade in grades:
            assert validate_grade(grade) is True

    def test_validate_letter_grade_lowercase(self):
        """Test lowercase letter grades."""
        assert validate_grade("a") is True
        assert validate_grade("b+") is True

    def test_validate_percentage_grade_zero(self):
        """Test validating percentage grade 0."""
        assert validate_grade("0") is True

    def test_validate_percentage_grade_hundred(self):
        """Test validating percentage grade 100."""
        assert validate_grade("100") is True

    def test_validate_percentage_grade_decimal(self):
        """Test validating decimal percentage grades."""
        assert validate_grade("95.5") is True

    def test_validate_percentage_grade_mid_range(self):
        """Test validating mid-range percentage."""
        assert validate_grade("75") is True

    def test_reject_invalid_grade_letter(self):
        """Test rejecting invalid letter grades."""
        with pytest.raises(ValidationError):
            validate_grade("G")

    def test_reject_grade_above_100(self):
        """Test rejecting grade above 100."""
        with pytest.raises(ValidationError):
            validate_grade("105")

    def test_reject_grade_below_0(self):
        """Test rejecting grade below 0."""
        with pytest.raises(ValidationError):
            validate_grade("-5")

    def test_reject_grade_invalid_format(self):
        """Test rejecting grade with invalid format."""
        with pytest.raises(ValidationError):
            validate_grade("ABC")

    def test_reject_multiple_plus_minus(self):
        """Test rejecting grade with multiple +/-."""
        with pytest.raises(ValidationError):
            validate_grade("A++")


class TestValidateFileExtension:
    """Tests for file extension validation."""

    def test_validate_file_extension_pdf(self):
        """Test validating PDF extension."""
        assert validate_file_extension("pdf") is True

    def test_validate_file_extension_with_dot(self):
        """Test validating extension with leading dot."""
        assert validate_file_extension(".pdf") is True

    def test_validate_file_extension_docx(self):
        """Test validating DOCX extension."""
        assert validate_file_extension("docx") is True

    def test_validate_file_extension_allowed_list(self):
        """Test validating against allowed list."""
        allowed = ["pdf", "docx", "xlsx"]
        assert validate_file_extension("pdf", allowed=allowed) is True

    def test_reject_extension_not_in_allowed(self):
        """Test rejecting extension not in allowed list."""
        allowed = ["pdf", "docx"]
        with pytest.raises(ValidationError):
            validate_file_extension("exe", allowed=allowed)

    def test_reject_empty_extension(self):
        """Test rejecting empty extension."""
        with pytest.raises(ValidationError):
            validate_file_extension("")

    def test_reject_extension_only_dot(self):
        """Test rejecting extension that is only a dot."""
        with pytest.raises(ValidationError):
            validate_file_extension(".")

    def test_validate_extension_case_insensitive(self):
        """Test extension validation is case insensitive."""
        assert validate_file_extension("PDF") is True
        assert validate_file_extension("DocX") is True

    def test_validate_extension_common_formats(self):
        """Test common file extensions."""
        common_extensions = ["pdf", "docx", "doc", "xlsx", "pptx", "txt", "csv", "jpg", "png"]
        for ext in common_extensions:
            assert validate_file_extension(ext) is True

    def test_reject_blocked_extension(self):
        """Test rejecting blocked extensions."""
        blocked = ["exe", "bat", "cmd", "sh"]
        for ext in blocked:
            with pytest.raises(ValidationError):
                validate_file_extension(ext, blocked=blocked)

    def test_validate_archive_extensions(self):
        """Test archive file extensions."""
        assert validate_file_extension("zip") is True
        assert validate_file_extension("rar") is True
        assert validate_file_extension("7z") is True
