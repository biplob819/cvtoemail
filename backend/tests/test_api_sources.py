"""Integration tests for source CRUD endpoints and Scan Now."""

import pytest
from unittest.mock import patch, AsyncMock


# ---------------------------------------------------------------------------
# POST /api/sources -- Create source
# ---------------------------------------------------------------------------

class TestCreateSource:
    """Tests for POST /api/sources."""

    @pytest.mark.integration
    async def test_create_source_success(self, client):
        """Should create a new source and return 201."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            resp = await client.post("/api/sources", json={
                "url": "https://create-test.com/careers",
                "portal_name": "Create Test",
                "filters_description": "Remote roles",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["url"] == "https://create-test.com/careers"
            assert data["portal_name"] == "Create Test"
            assert data["filters_description"] == "Remote roles"
            assert data["is_active"] is True
            assert data["jobs_found"] == 0

    @pytest.mark.integration
    async def test_create_source_duplicate_url(self, client):
        """Should reject duplicate URLs with 409."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            # Create first source
            await client.post("/api/sources", json={
                "url": "https://dup-test.com/careers",
                "portal_name": "Dup Test",
            })

            # Try to create duplicate
            resp = await client.post("/api/sources", json={
                "url": "https://dup-test.com/careers",
                "portal_name": "Dup Test 2",
            })
            assert resp.status_code == 409
            assert "already being monitored" in resp.json()["detail"]

    @pytest.mark.integration
    async def test_create_source_invalid_url(self, client):
        """Should reject invalid URLs with 422."""
        resp = await client.post("/api/sources", json={
            "url": "not-a-url",
            "portal_name": "Bad URL",
        })
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_source_missing_name(self, client):
        """Should reject missing portal name with 422."""
        resp = await client.post("/api/sources", json={
            "url": "https://example.com/careers",
            "portal_name": "",
        })
        assert resp.status_code == 422

    @pytest.mark.integration
    async def test_create_source_optional_filters(self, client):
        """Should accept a source without filters_description."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            resp = await client.post("/api/sources", json={
                "url": "https://no-filter.com/careers",
                "portal_name": "No Filter Test",
            })
            assert resp.status_code == 201
            assert resp.json()["filters_description"] in ("", None)


# ---------------------------------------------------------------------------
# GET /api/sources -- List sources
# ---------------------------------------------------------------------------

class TestListSources:
    """Tests for GET /api/sources."""

    @pytest.mark.integration
    async def test_list_sources_empty(self, client):
        """Should return empty list when no sources exist."""
        resp = await client.get("/api/sources")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.integration
    async def test_list_sources_with_data(self, client):
        """Should return all sources."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            await client.post("/api/sources", json={
                "url": "https://list-test-1.com/careers",
                "portal_name": "List Test 1",
            })
            await client.post("/api/sources", json={
                "url": "https://list-test-2.com/careers",
                "portal_name": "List Test 2",
            })

        resp = await client.get("/api/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        urls = [s["url"] for s in data]
        assert "https://list-test-1.com/careers" in urls
        assert "https://list-test-2.com/careers" in urls


# ---------------------------------------------------------------------------
# GET /api/sources/:id -- Get single source
# ---------------------------------------------------------------------------

class TestGetSource:
    """Tests for GET /api/sources/:id."""

    @pytest.mark.integration
    async def test_get_source_success(self, client):
        """Should return a specific source by ID."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://get-test.com/careers",
                "portal_name": "Get Test",
            })
            source_id = create_resp.json()["id"]

        resp = await client.get(f"/api/sources/{source_id}")
        assert resp.status_code == 200
        assert resp.json()["portal_name"] == "Get Test"

    @pytest.mark.integration
    async def test_get_source_not_found(self, client):
        """Should return 404 for non-existent source."""
        resp = await client.get("/api/sources/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/sources/:id -- Update source
# ---------------------------------------------------------------------------

class TestUpdateSource:
    """Tests for PUT /api/sources/:id."""

    @pytest.mark.integration
    async def test_update_source_name(self, client):
        """Should update the portal name."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://update-name.com/careers",
                "portal_name": "Old Name",
            })
            source_id = create_resp.json()["id"]

        resp = await client.put(f"/api/sources/{source_id}", json={
            "portal_name": "New Name",
        })
        assert resp.status_code == 200
        assert resp.json()["portal_name"] == "New Name"

    @pytest.mark.integration
    async def test_update_source_toggle_active(self, client):
        """Should toggle is_active status."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://toggle-test.com/careers",
                "portal_name": "Toggle Test",
            })
            source_id = create_resp.json()["id"]

        resp = await client.put(f"/api/sources/{source_id}", json={
            "is_active": False,
        })
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    @pytest.mark.integration
    async def test_update_source_duplicate_url(self, client):
        """Should reject if updating URL to one that already exists."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            await client.post("/api/sources", json={
                "url": "https://existing-url.com/careers",
                "portal_name": "Existing",
            })
            create_resp = await client.post("/api/sources", json={
                "url": "https://will-change.com/careers",
                "portal_name": "Will Change",
            })
            source_id = create_resp.json()["id"]

        resp = await client.put(f"/api/sources/{source_id}", json={
            "url": "https://existing-url.com/careers",
        })
        assert resp.status_code == 409

    @pytest.mark.integration
    async def test_update_source_not_found(self, client):
        """Should return 404 for non-existent source."""
        resp = await client.put("/api/sources/99999", json={
            "portal_name": "Ghost",
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/sources/:id -- Delete source
# ---------------------------------------------------------------------------

class TestDeleteSource:
    """Tests for DELETE /api/sources/:id."""

    @pytest.mark.integration
    async def test_delete_source_success(self, client):
        """Should delete a source and return confirmation."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://delete-me.com/careers",
                "portal_name": "Delete Me",
            })
            source_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/sources/{source_id}")
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Source deleted."

        # Verify it's gone
        get_resp = await client.get(f"/api/sources/{source_id}")
        assert get_resp.status_code == 404

    @pytest.mark.integration
    async def test_delete_source_not_found(self, client):
        """Should return 404 for non-existent source."""
        resp = await client.delete("/api/sources/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/sources/:id/scan -- Scan Now
# ---------------------------------------------------------------------------

class TestScanSource:
    """Tests for POST /api/sources/:id/scan."""

    @pytest.mark.integration
    async def test_scan_source_success(self, client):
        """Should scan and return results."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://scan-test.com/careers",
                "portal_name": "Scan Test",
            })
            source_id = create_resp.json()["id"]

        mock_jobs = [
            {"title": "Dev", "company": "Co", "location": "Remote",
             "url": "https://scan-test.com/jobs/1", "description": "A role"},
            {"title": "PM", "company": "Co", "location": "NYC",
             "url": "https://scan-test.com/jobs/2", "description": "Another role"},
        ]

        with patch("app.services.scraper.scrape_source", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_jobs

            resp = await client.post(f"/api/sources/{source_id}/scan")
            assert resp.status_code == 200
            data = resp.json()
            assert data["source_id"] == source_id
            assert data["jobs_found"] == 2
            assert data["new_jobs"] == 2

    @pytest.mark.integration
    async def test_scan_source_deduplicates(self, client):
        """Should not insert duplicate jobs on second scan."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://dedup-scan.com/careers",
                "portal_name": "Dedup Scan",
            })
            source_id = create_resp.json()["id"]

        mock_jobs = [
            {"title": "Dev", "company": "Co", "location": "Remote",
             "url": "https://dedup-scan.com/jobs/1", "description": "A role"},
        ]

        with patch("app.services.scraper.scrape_source", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_jobs

            # First scan
            resp1 = await client.post(f"/api/sources/{source_id}/scan")
            assert resp1.json()["new_jobs"] == 1

            # Second scan with same jobs
            resp2 = await client.post(f"/api/sources/{source_id}/scan")
            assert resp2.json()["new_jobs"] == 0  # No new jobs

    @pytest.mark.integration
    async def test_scan_paused_source_rejected(self, client):
        """Should reject scanning a paused source."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://paused-scan.com/careers",
                "portal_name": "Paused Scan",
            })
            source_id = create_resp.json()["id"]

        # Pause the source
        await client.put(f"/api/sources/{source_id}", json={"is_active": False})

        resp = await client.post(f"/api/sources/{source_id}/scan")
        assert resp.status_code == 400
        assert "paused" in resp.json()["detail"].lower()

    @pytest.mark.integration
    async def test_scan_source_not_found(self, client):
        """Should return 404 for non-existent source."""
        resp = await client.post("/api/sources/99999/scan")
        assert resp.status_code == 404

    @pytest.mark.integration
    async def test_scan_source_scraper_failure(self, client):
        """Should return 500 when scraper fails."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "OK"
            })()

            create_resp = await client.post("/api/sources", json={
                "url": "https://fail-scan.com/careers",
                "portal_name": "Fail Scan",
            })
            source_id = create_resp.json()["id"]

        with patch("app.services.scraper.scrape_source", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = RuntimeError("Connection refused")

            resp = await client.post(f"/api/sources/{source_id}/scan")
            assert resp.status_code == 500
            assert "Scraping failed" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# URL validation endpoint tests
# ---------------------------------------------------------------------------

class TestURLValidation:
    """Tests for URL validation endpoints."""

    @pytest.mark.integration
    async def test_check_url_reachable(self, client):
        """Should check if a URL is reachable."""
        with patch("app.routers.sources._check_url_reachable", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = type("R", (), {
                "reachable": True, "status_code": 200, "message": "URL is reachable."
            })()

            resp = await client.post("/api/sources/check-url", json={
                "url": "https://example.com",
            })
            assert resp.status_code == 200

    @pytest.mark.integration
    async def test_check_url_empty(self, client):
        """Should reject empty URL."""
        resp = await client.post("/api/sources/check-url", json={"url": ""})
        assert resp.status_code == 400
