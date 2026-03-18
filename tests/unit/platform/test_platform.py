"""Unit tests for platform abstraction layer."""

import os
import tempfile
from pathlib import Path

import pytest

from scholarr.core.platform import (
    PlatformDetector,
    get_disk_provider,
)


@pytest.fixture
def disk_provider():
    """Get the appropriate disk provider for the platform."""
    return get_disk_provider()


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestGetFreeSpace:
    """Tests for getting free disk space."""

    def test_get_free_space(self, disk_provider, temp_dir):
        """Test getting free disk space."""
        free_space = disk_provider.get_free_space(temp_dir)

        assert isinstance(free_space, int)
        assert free_space >= 0

    def test_free_space_is_reasonable(self, disk_provider, temp_dir):
        """Test that free space is a reasonable value."""
        free_space = disk_provider.get_free_space(temp_dir)

        # Free space should be in reasonable range (e.g., less than 1 PB)
        assert free_space < 1024 * 1024 * 1024 * 1024 * 1024

    def test_get_free_space_existing_path(self, disk_provider):
        """Test getting free space for existing path."""
        home_dir = os.path.expanduser("~")
        free_space = disk_provider.get_free_space(home_dir)

        assert isinstance(free_space, int)
        assert free_space >= 0


class TestGetTotalSpace:
    """Tests for getting total disk space."""

    def test_get_total_space(self, disk_provider, temp_dir):
        """Test getting total disk space."""
        total_space = disk_provider.get_total_space(temp_dir)

        assert isinstance(total_space, int)
        assert total_space > 0

    def test_total_space_greater_than_free(self, disk_provider, temp_dir):
        """Test that total space is greater than free space."""
        total_space = disk_provider.get_total_space(temp_dir)
        free_space = disk_provider.get_free_space(temp_dir)

        assert total_space >= free_space

    def test_total_space_is_reasonable(self, disk_provider, temp_dir):
        """Test that total space is a reasonable value."""
        total_space = disk_provider.get_total_space(temp_dir)

        # Total space should be reasonable (less than 1 PB)
        assert 0 < total_space < 1024 * 1024 * 1024 * 1024 * 1024


class TestFolderWritable:
    """Tests for checking folder writability."""

    def test_folder_writable(self, disk_provider, temp_dir):
        """Test checking if folder is writable."""
        is_writable = disk_provider.folder_writable(temp_dir)

        assert isinstance(is_writable, bool)
        assert is_writable is True

    def test_folder_writable_temp(self, disk_provider):
        """Test that temp directory is writable."""
        temp_dir = tempfile.gettempdir()
        is_writable = disk_provider.folder_writable(temp_dir)

        assert is_writable is True

    def test_folder_not_writable_nonexistent(self, disk_provider):
        """Test that non-existent folder is not writable."""
        is_writable = disk_provider.folder_writable("/nonexistent/path/12345")

        assert is_writable is False

    def test_folder_writable_with_file(self, disk_provider, temp_dir):
        """Test writability after creating file."""
        # Create a file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test")

        is_writable = disk_provider.folder_writable(temp_dir)

        assert is_writable is True


class TestCreateDirectory:
    """Tests for creating directories."""

    def test_create_directory(self, disk_provider, temp_dir):
        """Test creating a new directory."""
        new_dir = Path(temp_dir) / "new_folder"

        success = disk_provider.create_directory(str(new_dir))

        assert success is True
        assert new_dir.exists()

    def test_create_nested_directories(self, disk_provider, temp_dir):
        """Test creating nested directories."""
        nested_path = Path(temp_dir) / "level1" / "level2" / "level3"

        success = disk_provider.create_directory(str(nested_path))

        assert success is True
        assert nested_path.exists()

    def test_create_existing_directory(self, disk_provider, temp_dir):
        """Test creating a directory that already exists."""
        # Should not fail, just return True
        success = disk_provider.create_directory(temp_dir)

        assert success is True

    def test_create_directory_invalid_path(self, disk_provider):
        """Test creating directory with invalid path."""
        # Try to create in root (may fail depending on permissions)
        success = disk_provider.create_directory("/root_test_dir_12345")

        # Success depends on permissions, but should return bool
        assert isinstance(success, bool)


class TestMoveFile:
    """Tests for moving files."""

    def test_move_file(self, disk_provider, temp_dir):
        """Test moving a file."""
        source = Path(temp_dir) / "source.txt"
        dest = Path(temp_dir) / "dest.txt"

        source.write_text("test content")

        success = disk_provider.move_file(str(source), str(dest))

        assert success is True
        assert not source.exists()
        assert dest.exists()

    def test_move_file_to_subdirectory(self, disk_provider, temp_dir):
        """Test moving file to subdirectory."""
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()

        source = Path(temp_dir) / "file.txt"
        dest = subdir / "file.txt"

        source.write_text("test")

        success = disk_provider.move_file(str(source), str(dest))

        assert success is True
        assert dest.exists()

    def test_move_nonexistent_file(self, disk_provider, temp_dir):
        """Test moving non-existent file."""
        source = Path(temp_dir) / "nonexistent.txt"
        dest = Path(temp_dir) / "dest.txt"

        success = disk_provider.move_file(str(source), str(dest))

        # Should fail gracefully
        assert success is False

    def test_move_file_overwrites(self, disk_provider, temp_dir):
        """Test moving file over existing destination."""
        source = Path(temp_dir) / "source.txt"
        dest = Path(temp_dir) / "dest.txt"

        source.write_text("source content")
        dest.write_text("existing content")

        success = disk_provider.move_file(str(source), str(dest))

        assert success is True


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_platform_detection(self):
        """Test platform detection."""
        detector = PlatformDetector()
        current_os = detector.detect()

        assert current_os in ["Linux", "Windows", "Darwin"]

    def test_is_docker(self):
        """Test Docker detection."""
        detector = PlatformDetector()
        is_docker = detector.is_docker()

        # Should return bool regardless of environment
        assert isinstance(is_docker, bool)

    def test_platform_consistency(self):
        """Test platform detection consistency."""
        detector = PlatformDetector()

        os1 = detector.detect()
        os2 = detector.detect()

        assert os1 == os2


class TestGetMounts:
    """Tests for mount point detection."""

    def test_get_mounts(self, disk_provider):
        """Test getting mount points."""
        mounts = disk_provider.get_mounts()

        assert isinstance(mounts, list)
        # Should have at least one mount
        assert len(mounts) >= 1

    def test_mount_structure(self, disk_provider):
        """Test structure of mount information."""
        mounts = disk_provider.get_mounts()

        for mount in mounts:
            assert isinstance(mount, dict)
            assert "device" in mount or "mountpoint" in mount


class TestDiskSpaceCalculations:
    """Tests for disk space calculations."""

    def test_disk_usage_calculation(self, disk_provider, temp_dir):
        """Test disk usage calculation."""
        free = disk_provider.get_free_space(temp_dir)
        total = disk_provider.get_total_space(temp_dir)
        used = total - free

        assert used >= 0
        assert used <= total

    def test_disk_percentage_calculation(self, disk_provider, temp_dir):
        """Test disk usage percentage."""
        free = disk_provider.get_free_space(temp_dir)
        total = disk_provider.get_total_space(temp_dir)

        if total > 0:
            percent_used = ((total - free) / total) * 100
            assert 0 <= percent_used <= 100
