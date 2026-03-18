"""Integration providers for external platforms.

Built to support future connections to LMS platforms (Blackboard, Canvas, Moodle),
document tools (Microsoft Word, Google Docs), and direct database connections.
Each provider implements a common interface so adding new integrations is straightforward.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IntegrationType(Enum):
    """Types of integrations Scholarr can connect to."""
    LMS = "lms"
    DOCUMENT_TOOL = "document_tool"
    DATABASE = "database"
    CALENDAR = "calendar"
    STORAGE = "storage"


@dataclass
class IntegrationStatus:
    """Status info for an active integration."""
    provider_name: str
    provider_type: IntegrationType
    is_connected: bool
    last_sync: datetime | None = None
    last_error: str | None = None
    configuration_valid: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseIntegrationProvider(ABC):
    """Abstract base for all integration providers.

    Subclasses implement connect(), disconnect(), sync(), and get_status()
    to integrate with external platforms while maintaining a common interface.
    """

    def __init__(self, provider_name: str, provider_type: IntegrationType):
        """Initialize the provider."""
        self.provider_name = provider_name
        self.provider_type = provider_type
        self._is_connected = False
        self._last_sync: datetime | None = None
        self._last_error: str | None = None
        self._config: dict[str, Any] = {}

    @abstractmethod
    async def connect(self, config: dict[str, Any]) -> bool:
        """Connect to external service using provided configuration.

        Args:
            config: Dictionary with provider-specific connection params

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from external service.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    async def sync(self) -> dict[str, Any]:
        """Sync data from external service.

        Returns:
            Dictionary with sync results (items synced, errors, metadata)
        """
        pass

    @abstractmethod
    async def get_status(self) -> IntegrationStatus:
        """Get current status of this integration.

        Returns:
            IntegrationStatus object with connection and sync info
        """
        pass

    async def test_connection(self) -> bool:
        """Test if connection credentials are valid. Subclasses can override."""
        return self._is_connected

    def _set_last_error(self, error: str) -> None:
        """Record last error that occurred."""
        self._last_error = error

    def _clear_last_error(self) -> None:
        """Clear any recorded errors."""
        self._last_error = None


class IntegrationRegistry:
    """Registry for managing available and active integration providers."""

    def __init__(self):
        """Initialize the registry."""
        self._providers: dict[str, BaseIntegrationProvider] = {}
        self._available_providers: dict[str, type] = {}

    def register_available(self, provider_name: str, provider_class: type) -> None:
        """Register a provider class as available.

        Args:
            provider_name: Name to register provider under
            provider_class: The provider class (must inherit from BaseIntegrationProvider)
        """
        self._available_providers[provider_name] = provider_class

    def register_active(self, provider_name: str, provider: BaseIntegrationProvider) -> None:
        """Register an active provider instance.

        Args:
            provider_name: Name to register provider under
            provider: Initialized provider instance
        """
        self._providers[provider_name] = provider

    def get_provider(self, provider_name: str) -> BaseIntegrationProvider | None:
        """Get an active provider by name.

        Args:
            provider_name: Name of the provider to retrieve

        Returns:
            Provider instance if active, None otherwise
        """
        return self._providers.get(provider_name)

    def get_available_provider_class(self, provider_name: str) -> type | None:
        """Get an available provider class by name.

        Args:
            provider_name: Name of the provider to retrieve

        Returns:
            Provider class if available, None otherwise
        """
        return self._available_providers.get(provider_name)

    def list_active_providers(self) -> list[str]:
        """Get list of all active provider names.

        Returns:
            List of active provider names
        """
        return list(self._providers.keys())

    def list_available_providers(self) -> list[str]:
        """Get list of all available provider names.

        Returns:
            List of available provider names
        """
        return list(self._available_providers.keys())

    async def get_all_statuses(self) -> dict[str, IntegrationStatus]:
        """Get status for all active providers.

        Returns:
            Dictionary mapping provider names to their status
        """
        statuses = {}
        for name, provider in self._providers.items():
            try:
                statuses[name] = await provider.get_status()
            except Exception as e:
                # If we can't get status, create a minimal one
                statuses[name] = IntegrationStatus(
                    provider_name=name,
                    provider_type=provider.provider_type,
                    is_connected=False,
                    last_error=str(e)
                )
        return statuses

    async def disconnect_all(self) -> dict[str, bool]:
        """Disconnect all active providers.

        Returns:
            Dictionary mapping provider names to disconnect success status
        """
        results = {}
        for name, provider in list(self._providers.items()):
            try:
                success = await provider.disconnect()
                results[name] = success
                if success:
                    del self._providers[name]
            except Exception:
                results[name] = False
        return results


# Global registry instance
_global_registry: IntegrationRegistry | None = None


def get_registry() -> IntegrationRegistry:
    """Get the global integration registry, creating it if needed."""
    global _global_registry
    if _global_registry is None:
        _global_registry = IntegrationRegistry()
    return _global_registry
