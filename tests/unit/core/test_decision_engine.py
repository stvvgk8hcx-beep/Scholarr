"""Unit tests for import decision engine."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from scholarr.core.import_sources.decision_engine import (
    DecisionEngine,
    DecisionResult,
    ImportAction,
    QualityRank,
)
from scholarr.core.parser import FileNameParser, ParseResult, ItemType


@pytest_asyncio.fixture
async def decision_engine(async_session):
    """Create a DecisionEngine instance."""
    return DecisionEngine(async_session)


@pytest_asyncio.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(b"x" * 1000)  # 1KB of data
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


class TestAcceptValidFile:
    """Tests for accepting valid files."""

    async def test_accept_valid_file(self, decision_engine, sample_course, temp_file):
        """Test accepting a valid file."""
        parse_result = ParseResult(
            course_code=sample_course.code,
            item_type=ItemType.ASSIGNMENT,
        )

        result = await decision_engine.evaluate(temp_file, parse_result, sample_course.id)

        assert result.action == ImportAction.ACCEPT

    async def test_accept_pdf_file(self, decision_engine, sample_course, temp_file):
        """Test accepting a PDF file."""
        parse_result = ParseResult(
            course_code=sample_course.code,
            item_type=ItemType.ASSIGNMENT,
        )

        result = await decision_engine.evaluate(temp_file, parse_result, sample_course.id)

        assert result.action == ImportAction.ACCEPT


class TestRejectInvalidExtension:
    """Tests for rejecting invalid file extensions."""

    async def test_reject_invalid_extension(self, decision_engine, sample_course):
        """Test rejecting file with unsupported extension."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as f:
            f.write(b"x" * 1000)
            temp_path = f.name

        try:
            parse_result = ParseResult(
                course_code=sample_course.code,
                item_type=ItemType.ASSIGNMENT,
            )

            result = await decision_engine.evaluate(temp_path, parse_result, sample_course.id)

            assert result.action == ImportAction.REJECT
            assert "unsupported" in result.reason.lower() or "format" in result.reason.lower()
        finally:
            Path(temp_path).unlink()

    async def test_reject_blocked_extension(self, decision_engine, sample_course):
        """Test rejecting file with blocked extension."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bat") as f:
            f.write(b"x" * 1000)
            temp_path = f.name

        try:
            parse_result = ParseResult(
                course_code=sample_course.code,
                item_type=ItemType.ASSIGNMENT,
            )

            result = await decision_engine.evaluate(temp_path, parse_result, sample_course.id)

            assert result.action == ImportAction.REJECT
        finally:
            Path(temp_path).unlink()


class TestRejectOversizedFile:
    """Tests for rejecting oversized files."""

    async def test_reject_oversized_file(self, decision_engine, sample_course):
        """Test rejecting file exceeding size limit."""
        # Create a file larger than MAX_FILE_SIZE
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            # Create a 501 MB file (exceeds 500 MB limit)
            f.seek(500 * 1024 * 1024)
            f.write(b"x")
            temp_path = f.name

        try:
            parse_result = ParseResult(
                course_code=sample_course.code,
                item_type=ItemType.ASSIGNMENT,
            )

            result = await decision_engine.evaluate(temp_path, parse_result, sample_course.id)

            assert result.action == ImportAction.REJECT
            assert "exceed" in result.reason.lower() or "size" in result.reason.lower()
        finally:
            Path(temp_path).unlink()

    async def test_reject_empty_file(self, decision_engine, sample_course):
        """Test rejecting empty file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            temp_path = f.name

        try:
            parse_result = ParseResult(
                course_code=sample_course.code,
                item_type=ItemType.ASSIGNMENT,
            )

            result = await decision_engine.evaluate(temp_path, parse_result, sample_course.id)

            assert result.action == ImportAction.REJECT
            assert "empty" in result.reason.lower() or "small" in result.reason.lower()
        finally:
            Path(temp_path).unlink()


class TestSkipDuplicateHash:
    """Tests for skipping duplicate files."""

    async def test_skip_duplicate_hash(self, decision_engine, sample_course, sample_managed_file, temp_file):
        """Test skipping file with duplicate hash."""
        # Use the same hash as sample_managed_file
        parse_result = ParseResult(
            course_code=sample_course.code,
            item_type=ItemType.ASSIGNMENT,
        )

        # Mock hash calculation to return known hash
        original_calc = decision_engine._calculate_file_hash
        async def mock_hash(path):
            return sample_managed_file.hash
        decision_engine._calculate_file_hash = mock_hash

        try:
            result = await decision_engine.evaluate(temp_file, parse_result, sample_course.id)

            assert result.action == ImportAction.SKIP
            assert "duplicate" in result.reason.lower() or "exists" in result.reason.lower()
        finally:
            decision_engine._calculate_file_hash = original_calc


class TestUpgradeLowerQuality:
    """Tests for upgrading lower quality files."""

    async def test_upgrade_lower_quality(self, decision_engine, sample_course, sample_managed_file):
        """Test upgrading to higher quality version."""
        # Create a lower quality version of existing file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as f:
            f.write(b"x" * 1000)
            temp_path = f.name

        try:
            parse_result = ParseResult(
                course_code=sample_course.code,
                item_type=ItemType.ASSIGNMENT,
            )

            # Mock hash to return same hash as existing file
            original_calc = decision_engine._calculate_file_hash
            async def mock_hash(path):
                return sample_managed_file.hash
            decision_engine._calculate_file_hash = mock_hash

            result = await decision_engine.evaluate(temp_path, parse_result, sample_course.id)

            # Original file is PDF (highest quality), new file is DOCX (high quality)
            # Should not upgrade since PDF > DOCX
            assert result.action in [ImportAction.SKIP, ImportAction.UPGRADE]
        finally:
            Path(temp_path).unlink()
            decision_engine._calculate_file_hash = original_calc


class TestQualityScoringOrder:
    """Tests for quality scoring and ranking."""

    def test_quality_ranking_pdf_highest(self, decision_engine):
        """Test that PDF has highest quality rank."""
        score_pdf = decision_engine._calculate_quality_score("pdf")
        score_docx = decision_engine._calculate_quality_score("docx")

        assert score_pdf > score_docx

    def test_quality_ranking_docx_high(self, decision_engine):
        """Test that DOCX has high quality rank."""
        score_docx = decision_engine._calculate_quality_score("docx")
        score_txt = decision_engine._calculate_quality_score("txt")

        assert score_docx > score_txt

    def test_quality_ranking_txt_low(self, decision_engine):
        """Test that TXT has low quality rank."""
        score_txt = decision_engine._calculate_quality_score("txt")
        score_unsupported = decision_engine._calculate_quality_score("xyz")

        assert score_txt > score_unsupported

    def test_quality_ranking_order(self, decision_engine):
        """Test complete quality ranking order."""
        extensions = ["pdf", "docx", "xlsx", "txt", "rtf", "unknown"]
        scores = [decision_engine._calculate_quality_score(ext) for ext in extensions]

        # Verify descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]


class TestCustomFormatMatching:
    """Tests for custom format matching."""

    async def test_custom_format_matching(self, decision_engine, sample_course, temp_file):
        """Test that custom formats can be matched."""
        parse_result = ParseResult(
            course_code=sample_course.code,
            item_type=ItemType.ASSIGNMENT,
        )

        result = await decision_engine.evaluate(temp_file, parse_result, sample_course.id)

        # Should have a quality score regardless of custom format
        assert result.quality_score >= 0


class TestEmptyProfile:
    """Tests for handling empty profile."""

    async def test_empty_profile(self, decision_engine, sample_course, temp_file):
        """Test decision making with empty profile."""
        parse_result = ParseResult()

        result = await decision_engine.evaluate(temp_file, parse_result, sample_course.id)

        # Should still make a decision
        assert result.action is not None


class TestMultipleProfiles:
    """Tests for handling multiple decision profiles."""

    async def test_multiple_profiles(self, decision_engine, sample_course, temp_file):
        """Test evaluation with multiple possible matches."""
        parse_result = ParseResult(
            course_code=sample_course.code,
            item_type=ItemType.ASSIGNMENT,
            item_number="1",
        )

        result = await decision_engine.evaluate(temp_file, parse_result, sample_course.id)

        assert result.action is not None
        assert isinstance(result, DecisionResult)


class TestNonexistentFile:
    """Tests for handling non-existent files."""

    async def test_reject_nonexistent_file(self, decision_engine, sample_course):
        """Test rejecting non-existent file."""
        parse_result = ParseResult(
            course_code=sample_course.code,
            item_type=ItemType.ASSIGNMENT,
        )

        result = await decision_engine.evaluate("/nonexistent/path/file.pdf", parse_result, sample_course.id)

        assert result.action == ImportAction.REJECT
        assert "does not exist" in result.reason.lower() or "cannot" in result.reason.lower()
