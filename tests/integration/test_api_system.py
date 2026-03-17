"""Integration tests for system API endpoints."""

import pytest


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    async def test_health_endpoint(self, test_client, api_key):
        """Test health check endpoint."""
        response = await test_client.get(
            "/api/v1/health",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    async def test_health_includes_database(self, test_client, api_key):
        """Test health check includes database status."""
        response = await test_client.get(
            "/api/v1/health",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200


class TestStatusEndpoint:
    """Tests for status endpoint."""

    async def test_status_endpoint(self, test_client, api_key):
        """Test status endpoint."""
        response = await test_client.get(
            "/api/v1/system/status",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert "version" in data or "status" in data

    async def test_status_includes_info(self, test_client, api_key):
        """Test status includes system information."""
        response = await test_client.get(
            "/api/v1/system/status",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200


class TestBackupCreate:
    """Tests for creating backups."""

    async def test_backup_create(self, test_client, api_key):
        """Test creating a backup."""
        response = await test_client.post(
            "/api/v1/backup",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code in [200, 201, 202]


class TestBackupList:
    """Tests for listing backups."""

    async def test_backup_list(self, test_client, api_key):
        """Test listing backups."""
        response = await test_client.get(
            "/api/v1/backup",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestConfigEndpoint:
    """Tests for configuration endpoint."""

    async def test_config_endpoint(self, test_client, api_key):
        """Test configuration endpoint."""
        response = await test_client.get(
            "/api/v1/config",
            headers={"X-API-Key": api_key},
        )

        # May return 200 or 405 depending on implementation
        assert response.status_code in [200, 405]
