"""Unit tests for filename parser."""

import pytest

from scholarr.core.parser import FileNameParser, ItemType


@pytest.fixture
def parser():
    """Create a FileNameParser instance."""
    return FileNameParser()


class TestParseStandardFormat:
    """Tests for parsing standard filename format."""

    def test_parse_standard_format(self, parser):
        """Test parsing standard format: BCS310_Lab3_BinarySearchTrees.pdf"""
        filename = "BCS310_Lab3_BinarySearchTrees.pdf"

        result = parser.parse(filename)

        assert result.course_code == "BCS310"
        assert result.item_type == ItemType.LAB
        assert result.item_number == "3"
        assert result.topic == "BinarySearchTrees"

    def test_parse_assignment_format(self, parser):
        """Test parsing assignment format: Assignment 3 - Data Structures.docx"""
        filename = "Assignment 3 - Data Structures.docx"

        result = parser.parse(filename)

        assert result.item_type == ItemType.ASSIGNMENT
        assert result.item_number == "3"

    def test_parse_exam_format(self, parser):
        """Test parsing exam format: MAT235 Exam 2 Solutions.pdf"""
        filename = "MAT235 Exam 2 Solutions.pdf"

        result = parser.parse(filename)

        assert result.course_code == "MAT235"
        assert result.item_type == ItemType.EXAM
        assert result.item_number == "2"

    def test_parse_lecture_notes(self, parser):
        """Test parsing lecture notes: Lecture_Notes_Week5.pdf"""
        filename = "Lecture_Notes_Week5.pdf"

        result = parser.parse(filename)

        assert result.item_type == ItemType.LECTURE
        assert "Week5" in (result.topic or "")

    def test_parse_dash_format(self, parser):
        """Test parsing dash-separated format: lab03-binary-search.py"""
        filename = "lab03-binary-search.py"

        result = parser.parse(filename)

        assert result.item_type == ItemType.LAB
        assert result.item_number == "03"

    def test_parse_no_course_code(self, parser):
        """Test parsing when course code is missing."""
        filename = "General_Notes.pdf"

        result = parser.parse(filename)

        assert result.course_code is None
        # Should still detect item type
        assert result.item_type == ItemType.NOTES

    def test_parse_with_date(self, parser):
        """Test parsing with date hint."""
        filename = "BCS310_Lab3_2024-03-15.pdf"

        result = parser.parse(filename)

        assert result.course_code == "BCS310"
        assert result.date_hint == "2024-03-15"

    def test_parse_with_version_hint_draft(self, parser):
        """Test parsing with version hint (draft)."""
        filename = "Assignment3_draft.docx"

        result = parser.parse(filename)

        assert result.version == "draft"

    def test_parse_with_version_hint_final(self, parser):
        """Test parsing with version hint (final)."""
        filename = "Essay_final.pdf"

        result = parser.parse(filename)

        assert result.version == "final"

    def test_parse_with_version_hint_graded(self, parser):
        """Test parsing with version hint (graded)."""
        filename = "Lab_graded.pdf"

        result = parser.parse(filename)

        assert result.version == "graded"


class TestConfidenceScoring:
    """Tests for confidence score calculation."""

    def test_confidence_scoring_high(self, parser):
        """Test high confidence parsing."""
        filename = "BCS310_Assignment3_BinarySearchTrees.pdf"

        result = parser.parse(filename)

        assert result.confidence_score > 0.7

    def test_confidence_scoring_medium(self, parser):
        """Test medium confidence parsing."""
        filename = "Assignment3.pdf"

        result = parser.parse(filename)

        assert 0.3 < result.confidence_score <= 0.7

    def test_confidence_scoring_low(self, parser):
        """Test low confidence parsing."""
        filename = "file123.txt"

        result = parser.parse(filename)

        assert result.confidence_score <= 0.3


class TestAllItemTypesDetection:
    """Tests for detecting all item types."""

    def test_assignment_detection(self, parser):
        """Test assignment type detection."""
        for keyword in ["Assignment", "assign", "hw", "homework"]:
            filename = f"BCS310_{keyword}1.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.ASSIGNMENT, f"Failed for {keyword}"

    def test_lab_detection(self, parser):
        """Test lab type detection."""
        for keyword in ["Lab", "lab", "practical"]:
            filename = f"CSC{keyword}1.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.LAB, f"Failed for {keyword}"

    def test_exam_detection(self, parser):
        """Test exam type detection."""
        for keyword in ["Exam", "Test", "Midterm", "Final"]:
            filename = f"MAT235{keyword}.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.EXAM, f"Failed for {keyword}"

    def test_lecture_detection(self, parser):
        """Test lecture type detection."""
        for keyword in ["Lecture", "Lec"]:
            filename = f"PHY{keyword}1.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.LECTURE, f"Failed for {keyword}"

    def test_paper_detection(self, parser):
        """Test paper type detection."""
        for keyword in ["Paper", "Essay"]:
            filename = f"ENG{keyword}1.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.PAPER, f"Failed for {keyword}"

    def test_project_detection(self, parser):
        """Test project type detection."""
        filename = "CSC_Project1.pdf"
        result = parser.parse(filename)
        assert result.item_type == ItemType.PROJECT

    def test_notes_detection(self, parser):
        """Test notes type detection."""
        for keyword in ["Notes", "note"]:
            filename = f"ChemistryClassroom{keyword}.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.NOTES, f"Failed for {keyword}"

    def test_syllabus_detection(self, parser):
        """Test syllabus type detection."""
        filename = "BCS310_Syllabus.pdf"
        result = parser.parse(filename)
        assert result.item_type == ItemType.SYLLABUS

    def test_textbook_detection(self, parser):
        """Test textbook type detection."""
        filename = "Discrete_Mathematics_Textbook.pdf"
        result = parser.parse(filename)
        assert result.item_type == ItemType.TEXTBOOK

    def test_slides_detection(self, parser):
        """Test slides type detection."""
        for keyword in ["Slides", "Slide"]:
            filename = f"Lecture{keyword}_Week1.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.SLIDES, f"Failed for {keyword}"

    def test_tutorial_detection(self, parser):
        """Test tutorial type detection."""
        for keyword in ["Tutorial", "Tut"]:
            filename = f"Python{keyword}1.pdf"
            result = parser.parse(filename)
            assert result.item_type == ItemType.TUTORIAL, f"Failed for {keyword}"

    def test_quiz_detection(self, parser):
        """Test quiz type detection."""
        filename = "BCS310_Quiz_Week1.pdf"
        result = parser.parse(filename)
        assert result.item_type == ItemType.QUIZ


class TestCaseInsensitive:
    """Tests for case-insensitive parsing."""

    def test_case_insensitive_course_code(self, parser):
        """Test case-insensitive course code detection."""
        filenames = ["bcs310_lab1.pdf", "BCS310_LAB1.pdf", "Bcs310_Lab1.pdf"]

        for filename in filenames:
            result = parser.parse(filename)
            assert result.course_code == "bcs310" or result.course_code == "BCS310"

    def test_case_insensitive_item_type(self, parser):
        """Test case-insensitive item type detection."""
        filenames = ["assignment1.pdf", "ASSIGNMENT1.pdf", "Assignment1.pdf"]

        for filename in filenames:
            result = parser.parse(filename)
            assert result.item_type == ItemType.ASSIGNMENT

    def test_case_insensitive_version(self, parser):
        """Test case-insensitive version detection."""
        filenames = ["lab_draft.pdf", "lab_DRAFT.pdf", "lab_Draft.pdf"]

        for filename in filenames:
            result = parser.parse(filename)
            assert result.version is not None


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_parse_empty_filename(self, parser):
        """Test parsing empty filename."""
        result = parser.parse("")

        assert result.course_code is None
        assert result.item_type is None

    def test_parse_only_extension(self, parser):
        """Test parsing filename with only extension."""
        result = parser.parse(".pdf")

        assert result.course_code is None
        assert result.item_type is None

    def test_parse_special_characters(self, parser):
        """Test parsing with special characters."""
        filename = "BCS310_Lab3_@#$%^&.pdf"

        result = parser.parse(filename)

        assert result.course_code == "BCS310"

    def test_parse_unicode_characters(self, parser):
        """Test parsing with unicode characters."""
        filename = "BCS310_Lab_Ñ_Çedille.pdf"

        result = parser.parse(filename)

        # Should handle unicode gracefully
        assert result is not None

    def test_parse_very_long_filename(self, parser):
        """Test parsing very long filename."""
        filename = "BCS310_" + "a" * 200 + ".pdf"

        result = parser.parse(filename)

        assert result.course_code == "BCS310"

    def test_multiple_course_codes(self, parser):
        """Test parsing with multiple potential course codes."""
        filename = "BCS310_AND_MAT235_Assignment.pdf"

        result = parser.parse(filename)

        # Should detect the first one
        assert result.course_code in ["BCS310", "MAT235"]

    def test_parse_numbered_format(self, parser):
        """Test parsing when item is referenced only by number."""
        filename = "BCS310_3_BinarySearch.pdf"

        result = parser.parse(filename)

        assert result.course_code == "BCS310"
        assert result.item_number == "3"
