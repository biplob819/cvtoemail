"""Integration tests for the health check endpoint."""

import pytest


class TestHealthCheck:
    """Tests for GET /api/health."""

    @pytest.mark.integration
    async def test_health_returns_200(self, client):
        """Health check should return 200 OK."""
        response = await client.get("/api/health")
        assert response.status_code == 200

    @pytest.mark.integration
    async def test_health_returns_ok_status(self, client):
        """Health check response should include status: ok."""
        response = await client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.integration
    async def test_health_returns_app_name(self, client):
        """Health check should include the application name."""
        response = await client.get("/api/health")
        data = response.json()
        assert "app" in data
        assert data["app"] == "Auto Job Apply"
