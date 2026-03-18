"""Cross-platform OS abstraction layer for Scholarr."""

import os
import platform
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

import psutil


class DiskProvider(ABC):
    """Base class for disk operations."""

    @abstractmethod
    def get_free_space(self, path: str) -> int:
        """Get free disk space in bytes."""
        pass

    @abstractmethod
    def get_total_space(self, path: str) -> int:
        """Get total disk space in bytes."""
        pass

    @abstractmethod
    def folder_writable(self, path: str) -> bool:
        """Check if folder is writable."""
        pass

    @abstractmethod
    def get_mounts(self) -> list[dict]:
        """Get list of mounted volumes."""
        pass

    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        pass

    @abstractmethod
    def move_file(self, src: str, dst: str) -> bool:
        """Move a file."""
        pass


class LinuxDiskProvider(DiskProvider):
    """Disk provider for Linux."""

    def get_free_space(self, path: str) -> int:
        """Get free disk space in bytes."""
        try:
            stats = psutil.disk_usage(path)
            return stats.free
        except (OSError, ValueError):
            return 0

    def get_total_space(self, path: str) -> int:
        """Get total disk space in bytes."""
        try:
            stats = psutil.disk_usage(path)
            return stats.total
        except (OSError, ValueError):
            return 0

    def folder_writable(self, path: str) -> bool:
        """Check if folder is writable."""
        return os.path.exists(path) and os.access(path, os.W_OK)

    def get_mounts(self) -> list[dict]:
        """Get list of mounted volumes."""
        mounts = []
        for partition in psutil.disk_partitions():
            mounts.append(
                {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                }
            )
        return mounts

    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def move_file(self, src: str, dst: str) -> bool:
        """Move a file."""
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False


class WindowsDiskProvider(DiskProvider):
    """Disk provider for Windows."""

    def get_free_space(self, path: str) -> int:
        """Get free disk space in bytes."""
        try:
            stats = psutil.disk_usage(path)
            return stats.free
        except (OSError, ValueError):
            return 0

    def get_total_space(self, path: str) -> int:
        """Get total disk space in bytes."""
        try:
            stats = psutil.disk_usage(path)
            return stats.total
        except (OSError, ValueError):
            return 0

    def folder_writable(self, path: str) -> bool:
        """Check if folder is writable."""
        return os.path.exists(path) and os.access(path, os.W_OK)

    def get_mounts(self) -> list[dict]:
        """Get list of mounted volumes."""
        mounts = []
        for partition in psutil.disk_partitions():
            mounts.append(
                {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                }
            )
        return mounts

    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def move_file(self, src: str, dst: str) -> bool:
        """Move a file."""
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False


class MacOSDiskProvider(DiskProvider):
    """Disk provider for macOS."""

    def get_free_space(self, path: str) -> int:
        """Get free disk space in bytes."""
        try:
            stats = psutil.disk_usage(path)
            return stats.free
        except (OSError, ValueError):
            return 0

    def get_total_space(self, path: str) -> int:
        """Get total disk space in bytes."""
        try:
            stats = psutil.disk_usage(path)
            return stats.total
        except (OSError, ValueError):
            return 0

    def folder_writable(self, path: str) -> bool:
        """Check if folder is writable."""
        return os.path.exists(path) and os.access(path, os.W_OK)

    def get_mounts(self) -> list[dict]:
        """Get list of mounted volumes."""
        mounts = []
        for partition in psutil.disk_partitions():
            mounts.append(
                {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                }
            )
        return mounts

    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def move_file(self, src: str, dst: str) -> bool:
        """Move a file."""
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False


class EnvironmentProvider:
    """Provider for environment and system information."""

    @staticmethod
    def get_os_name() -> str:
        """Get operating system name.

        Returns:
            str: OS name (Linux, Windows, Darwin, etc).
        """
        return platform.system()

    @staticmethod
    def get_os_version() -> str:
        """Get operating system version.

        Returns:
            str: OS version string.
        """
        return platform.release()

    @staticmethod
    def is_docker() -> bool:
        """Check if running in Docker.

        Returns:
            bool: True if running in Docker.
        """
        return os.path.exists("/.dockerenv") or os.path.exists("/run/.dockerenv")

    @staticmethod
    def get_runtime_dir() -> str:
        """Get runtime directory for temporary files.

        Returns:
            str: Path to runtime directory.
        """
        if os.name == "nt":  # Windows
            return os.environ.get("TEMP", "C:\\Windows\\Temp")
        else:  # Unix-like
            return os.environ.get("XDG_RUNTIME_DIR", "/tmp")

    @staticmethod
    def get_home_dir() -> str:
        """Get user home directory.

        Returns:
            str: Path to home directory.
        """
        return str(Path.home())

    @staticmethod
    def get_python_version() -> str:
        """Get Python version.

        Returns:
            str: Python version string.
        """
        return platform.python_version()


class PlatformFactory:
    """Factory for creating platform-specific providers."""

    @staticmethod
    def get_disk_provider() -> DiskProvider:
        """Get disk provider for current platform.

        Returns:
            DiskProvider: Platform-specific disk provider.
        """
        os_name = platform.system()

        if os_name == "Linux":
            return LinuxDiskProvider()
        elif os_name == "Windows":
            return WindowsDiskProvider()
        elif os_name == "Darwin":  # macOS
            return MacOSDiskProvider()
        else:
            return LinuxDiskProvider()

    @staticmethod
    def get_environment_provider() -> EnvironmentProvider:
        """Get environment provider.

        Returns:
            EnvironmentProvider: Environment provider instance.
        """
        return EnvironmentProvider()


def get_disk_provider() -> DiskProvider:
    """Get disk provider for current platform."""
    return PlatformFactory.get_disk_provider()


def get_environment_provider() -> EnvironmentProvider:
    """Get environment provider."""
    return PlatformFactory.get_environment_provider()


class PlatformDetector:
    """Platform detection helper used in tests and diagnostics."""

    def detect(self) -> str:
        """Return current OS name: Linux, Windows, or Darwin."""
        return platform.system()

    def is_docker(self) -> bool:
        """Return True if running inside a Docker container."""
        return EnvironmentProvider.is_docker()
