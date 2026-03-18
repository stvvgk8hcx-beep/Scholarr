"""Unit tests for file organization and naming."""

from datetime import datetime

import pytest

from scholarr.core.organizer import ColonReplacementFormat, FileNameBuilder, NamingContext


@pytest.fixture
def naming_context():
    """Create a sample naming context."""
    return NamingContext(
        semester="Fall 2024",
        term="Fall",
        year=2024,
        course_code="BCS310",
        course_name="Data Structures",
        course_section="01",
        professor="Dr. Smith",
        credits=3.0,
        item_type="Assignment",
        item_number="3",
        item_topic="Binary Search Trees",
        item_name="Assignment 3",
        due_date=datetime(2024, 10, 15),
        date_received=datetime(2024, 10, 14),
        grade=95.0,
        status="Complete",
        weight=10.0,
        file_type="PDF",
        file_format="pdf",
        original_filename="BCS310_Assignment3.pdf",
        extension="pdf",
        file_quality="highest",
        file_version=1,
    )


@pytest.fixture
def builder():
    """Create a FileNameBuilder instance."""
    return FileNameBuilder()


class TestBuildFilenameSimple:
    """Tests for simple filename building."""

    def test_build_filename_simple(self, builder, naming_context):
        """Test building a simple filename."""
        template = "{Item Name}.{Extension}"

        filename = builder.build_filename(template, naming_context)

        assert filename == "Assignment 3.pdf"

    def test_build_filename_course_and_item(self, builder, naming_context):
        """Test building filename with course and item."""
        template = "{Course Code}_{Item Number}_{Item Topic}.{Extension}"

        filename = builder.build_filename(template, naming_context)

        assert filename == "BCS310_3_Binary Search Trees.pdf"

    def test_build_filename_with_grade(self, builder, naming_context):
        """Test building filename with grade."""
        template = "{Item Name}_{Grade}.{Extension}"

        filename = builder.build_filename(template, naming_context)

        assert filename == "Assignment 3_95.0.pdf"


class TestBuildFilenameAllTokens:
    """Tests for complex filename templates."""

    def test_build_filename_with_all_tokens(self, builder, naming_context):
        """Test building filename with multiple token types."""
        template = "{Course Code}_{Item Number}_{Item Type}_{Grade}_{Status}"

        filename = builder.build_filename(template, naming_context)

        assert "BCS310" in filename
        assert "3" in filename
        assert "Assignment" in filename
        assert "95" in filename
        assert "Complete" in filename

    def test_build_filename_with_professor(self, builder, naming_context):
        """Test including professor in filename."""
        template = "{Course Code}_{Item Name}_{Professor}"

        filename = builder.build_filename(template, naming_context)

        assert "BCS310" in filename
        assert "Smith" in filename

    def test_build_filename_semester_token(self, builder, naming_context):
        """Test including semester information."""
        template = "{Semester}_{Course Code}_{Item Name}"

        filename = builder.build_filename(template, naming_context)

        assert "Fall 2024" in filename or "Fall" in filename


class TestZeroPaddedNumbers:
    """Tests for zero-padded number formatting."""

    def test_zero_padded_numbers(self, builder, naming_context):
        """Test zero-padding item numbers."""
        template = "{Item Number:00}_{Item Name}"

        filename = builder.build_filename(template, naming_context)

        assert "03_" in filename

    def test_zero_padded_different_lengths(self, builder):
        """Test zero-padding with different lengths."""
        context = NamingContext(item_number="5", item_name="Test")

        # Test various padding lengths
        templates = [
            ("{Item Number:00}", "05"),
            ("{Item Number:000}", "005"),
            ("{Item Number:0000}", "0005"),
        ]

        for template, expected_number in templates:
            filename = builder.build_filename(template, context)
            assert expected_number in filename


class TestFolderPathBuilding:
    """Tests for folder path construction."""

    def test_folder_path_building(self, builder, naming_context):
        """Test building folder paths."""
        template = "{Semester}/{Course Code}/{Item Type}"

        path = builder.build_path(template, naming_context)

        assert "Fall 2024" in path or "Fall" in path
        assert "BCS310" in path
        assert "Assignment" in path

    def test_folder_path_with_year(self, builder, naming_context):
        """Test folder path with year."""
        template = "{Year}/{Term}/{Course Code}"

        path = builder.build_path(template, naming_context)

        assert "2024" in path
        assert "Fall" in path
        assert "BCS310" in path

    def test_folder_path_nested(self, builder, naming_context):
        """Test deeply nested folder paths."""
        template = "Library/{Year}/{Semester}/{Course Code}/{Item Type}/{Item Number}"

        path = builder.build_path(template, naming_context)

        assert "Library" in path
        assert "2024" in path
        assert "BCS310" in path
        assert "3" in path


class TestIllegalCharacterReplacement:
    """Tests for handling illegal filename characters."""

    def test_illegal_character_replacement(self, builder):
        """Test replacing illegal characters."""
        context = NamingContext(
            course_name="Data: Structures & Analysis",
            item_name="Assignment | 3",
        )

        template = "{Course Name}_{Item Name}"
        filename = builder.build_filename(template, context)

        # Should not contain illegal characters
        assert ":" not in filename
        assert "|" not in filename or filename.count("|") == 0

    def test_colon_replacement_dash(self, builder):
        """Test colon replacement with dash."""
        context = NamingContext(item_name="Time: 10:30")

        template = "{Item Name}"
        filename = builder.build_filename(
            template, context, colon_format=ColonReplacementFormat.DASH
        )

        assert ":" not in filename
        assert "-" in filename

    def test_colon_replacement_underscore(self, builder):
        """Test colon replacement with underscore."""
        context = NamingContext(item_name="Time: 10:30")

        template = "{Item Name}"
        filename = builder.build_filename(
            template, context, colon_format=ColonReplacementFormat.UNDERSCORE
        )

        assert ":" not in filename
        assert "_" in filename

    def test_colon_replacement_space(self, builder):
        """Test colon replacement with space."""
        context = NamingContext(item_name="Time: 10:30")

        template = "{Item Name}"
        filename = builder.build_filename(
            template, context, colon_format=ColonReplacementFormat.SPACE
        )

        assert ":" not in filename

    def test_colon_replacement_remove(self, builder):
        """Test removing colons."""
        context = NamingContext(item_name="Time: 10:30")

        template = "{Item Name}"
        filename = builder.build_filename(
            template, context, colon_format=ColonReplacementFormat.REMOVE
        )

        assert ":" not in filename


class TestEmptyOptionalTokens:
    """Tests for handling empty optional tokens."""

    def test_empty_optional_tokens(self, builder):
        """Test handling of missing optional fields."""
        context = NamingContext(
            course_code="BCS310",
            item_name="Assignment",
            professor=None,  # Missing field
        )

        template = "{Course Code}_{Item Name}_{Professor}"
        filename = builder.build_filename(template, context)

        # Should handle missing token gracefully
        assert "BCS310" in filename
        assert "Assignment" in filename
        # Missing professor should not break the filename
        assert "_None" not in filename and filename[-1] != "_"

    def test_skip_missing_tokens(self, builder):
        """Test skipping entirely missing tokens."""
        context = NamingContext(
            course_code="MAT235",
            grade=None,
        )

        template = "{Course Code}_{Grade}"
        filename = builder.build_filename(template, context)

        assert "MAT235" in filename


class TestDateFormatting:
    """Tests for date token formatting."""

    def test_date_formatting_due_date(self, builder):
        """Test due date formatting."""
        context = NamingContext(
            due_date=datetime(2024, 10, 15),
            item_name="Assignment",
        )

        template = "{Item Name}_{Due Date}"
        filename = builder.build_filename(template, context, date_format="%Y-%m-%d")

        assert "2024-10-15" in filename

    def test_date_formatting_date_received(self, builder):
        """Test date received formatting."""
        context = NamingContext(
            date_received=datetime(2024, 10, 14),
            item_name="Submission",
        )

        template = "{Item Name}_{Date Received}"
        filename = builder.build_filename(template, context, date_format="%m/%d/%Y")

        assert "10/14/2024" in filename

    def test_custom_date_format(self, builder):
        """Test custom date format."""
        context = NamingContext(
            due_date=datetime(2024, 3, 15),
            item_name="Test",
        )

        template = "{Due Date}"
        filename = builder.build_filename(template, context, date_format="%d-%b-%Y")

        assert "15-Mar-2024" in filename


class TestSemesterToken:
    """Tests for semester token."""

    def test_semester_token(self, builder, naming_context):
        """Test semester token usage."""
        template = "{Semester}"

        result = builder.build_filename(template, naming_context)

        assert "Fall" in result or "2024" in result

    def test_term_token(self, builder, naming_context):
        """Test term token usage."""
        template = "{Term}"

        result = builder.build_filename(template, naming_context)

        assert result == "Fall"

    def test_year_token(self, builder, naming_context):
        """Test year token usage."""
        template = "{Year}"

        result = builder.build_filename(template, naming_context)

        assert result == "2024"


class TestCourseTokens:
    """Tests for course-related tokens."""

    def test_course_code_token(self, builder, naming_context):
        """Test course code token."""
        template = "{Course Code}"

        result = builder.build_filename(template, naming_context)

        assert result == "BCS310"

    def test_course_name_token(self, builder, naming_context):
        """Test course name token."""
        template = "{Course Name}"

        result = builder.build_filename(template, naming_context)

        assert result == "Data Structures"

    def test_course_section_token(self, builder, naming_context):
        """Test course section token."""
        template = "{Course Section}"

        result = builder.build_filename(template, naming_context)

        assert result == "01"


class TestItemTokens:
    """Tests for item-related tokens."""

    def test_item_type_token(self, builder, naming_context):
        """Test item type token."""
        template = "{Item Type}"

        result = builder.build_filename(template, naming_context)

        assert result == "Assignment"

    def test_item_number_token(self, builder, naming_context):
        """Test item number token."""
        template = "{Item Number}"

        result = builder.build_filename(template, naming_context)

        assert result == "3"

    def test_item_topic_token(self, builder, naming_context):
        """Test item topic token."""
        template = "{Item Topic}"

        result = builder.build_filename(template, naming_context)

        assert result == "Binary Search Trees"

    def test_item_name_token(self, builder, naming_context):
        """Test item name token."""
        template = "{Item Name}"

        result = builder.build_filename(template, naming_context)

        assert result == "Assignment 3"


class TestFileTokens:
    """Tests for file-related tokens."""

    def test_file_type_token(self, builder, naming_context):
        """Test file type token."""
        template = "{File Type}"

        result = builder.build_filename(template, naming_context)

        assert result == "PDF"

    def test_extension_token(self, builder, naming_context):
        """Test extension token."""
        template = "{Extension}"

        result = builder.build_filename(template, naming_context)

        assert result == "pdf"

    def test_file_quality_token(self, builder, naming_context):
        """Test file quality token."""
        template = "{File Quality}"

        result = builder.build_filename(template, naming_context)

        assert result == "highest"

    def test_file_version_token(self, builder, naming_context):
        """Test file version token."""
        template = "{File Version}"

        result = builder.build_filename(template, naming_context)

        assert result == "1"
