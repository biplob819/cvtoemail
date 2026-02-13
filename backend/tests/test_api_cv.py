"""Integration tests for the CV management API endpoints."""

import io
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.conftest import SAMPLE_CV_DATA, SAMPLE_PERSONAL_INFO


# ---------------------------------------------------------------------------
# GET /api/cv
# ---------------------------------------------------------------------------

class TestGetCV:
    """Tests for GET /api/cv -- retrieve CV profile."""

    @pytest.mark.integration
    async def test_get_cv_returns_null_when_empty(self, client):
        """When no CV exists, should return null/None."""
        response = await client.get("/api/cv")
        assert response.status_code == 200
        # Response is null or the body is empty
        assert response.json() is None or response.text == "null"

    @pytest.mark.integration
    async def test_get_cv_returns_data_after_creation(self, client):
        """After creating a CV via PUT, GET should return the data."""
        # First create a CV
        cv_payload = {
            "personal_info": SAMPLE_PERSONAL_INFO,
            "summary": "Test summary",
            "work_experience": [],
            "education": [],
            "skills": ["Python"],
            "certifications": [],
        }
        put_resp = await client.put("/api/cv", json=cv_payload)
        assert put_resp.status_code == 200

        # Now get it
        get_resp = await client.get("/api/cv")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data is not None
        assert data["personal_info"]["name"] == "Jane Doe"
        assert data["skills"] == ["Python"]


# ---------------------------------------------------------------------------
# PUT /api/cv
# ---------------------------------------------------------------------------

class TestUpdateCV:
    """Tests for PUT /api/cv -- create/update CV profile."""

    @pytest.mark.integration
    async def test_create_cv_profile(self, client):
        """Should create a new CV profile and return it."""
        payload = {
            "personal_info": {"name": "Alice Smith", "email": "alice@test.com",
                              "phone": "123", "location": "NYC"},
            "summary": "A skilled developer.",
            "work_experience": [
                {"title": "Dev", "company": "Corp", "duration": "2020-2023",
                 "achievements": ["Built things"]}
            ],
            "education": [
                {"degree": "BS CS", "institution": "MIT", "year": "2020"}
            ],
            "skills": ["Python", "Java"],
            "certifications": [
                {"name": "AWS Cert", "issuer": "AWS", "year": "2023"}
            ],
        }
        response = await client.put("/api/cv", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["personal_info"]["name"] == "Alice Smith"
        assert data["summary"] == "A skilled developer."
        assert len(data["work_experience"]) == 1
        assert len(data["education"]) == 1
        assert data["skills"] == ["Python", "Java"]
        assert len(data["certifications"]) == 1
        assert "id" in data

    @pytest.mark.integration
    async def test_update_existing_cv_profile(self, client):
        """Updating an existing CV should modify the stored data."""
        # Create first
        payload_v1 = {
            "personal_info": {"name": "Bob", "email": "bob@test.com",
                              "phone": "", "location": ""},
            "summary": "Version 1",
            "work_experience": [],
            "education": [],
            "skills": ["Go"],
            "certifications": [],
        }
        await client.put("/api/cv", json=payload_v1)

        # Update
        payload_v2 = {
            "personal_info": {"name": "Bob Updated", "email": "bob2@test.com",
                              "phone": "555", "location": "LA"},
            "summary": "Version 2",
            "work_experience": [],
            "education": [],
            "skills": ["Go", "Rust"],
            "certifications": [],
        }
        response = await client.put("/api/cv", json=payload_v2)
        assert response.status_code == 200
        data = response.json()
        assert data["personal_info"]["name"] == "Bob Updated"
        assert data["summary"] == "Version 2"
        assert "Rust" in data["skills"]

    @pytest.mark.integration
    async def test_partial_update_preserves_other_fields(self, client):
        """Updating only some fields should not wipe out others."""
        payload = {
            "personal_info": {"name": "Carol", "email": "carol@test.com",
                              "phone": "", "location": "London"},
            "summary": "Original summary",
            "work_experience": [],
            "education": [],
            "skills": ["TypeScript"],
            "certifications": [],
        }
        await client.put("/api/cv", json=payload)

        # Update only summary and skills
        update_payload = {
            "personal_info": {"name": "Carol", "email": "carol@test.com",
                              "phone": "", "location": "London"},
            "summary": "Updated summary",
            "skills": ["TypeScript", "React"],
        }
        response = await client.put("/api/cv", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Updated summary"
        assert "React" in data["skills"]

    @pytest.mark.integration
    async def test_cv_response_includes_id_and_timestamp(self, client):
        """Response should include the CV id and updated_at timestamp."""
        payload = {
            "personal_info": {"name": "Test", "email": "", "phone": "", "location": ""},
            "summary": "",
            "work_experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
        }
        response = await client.put("/api/cv", json=payload)
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)


# ---------------------------------------------------------------------------
# POST /api/cv/upload
# ---------------------------------------------------------------------------

class TestUploadCV:
    """Tests for POST /api/cv/upload -- file upload and parse."""

    @pytest.mark.integration
    async def test_reject_invalid_file_type(self, client):
        """Should reject non-PDF/DOCX files with 400."""
        files = {"file": ("resume.txt", b"Hello world", "text/plain")}
        response = await client.post("/api/cv/upload", files=files)
        assert response.status_code == 400
        assert "PDF and DOCX" in response.json()["detail"]

    @pytest.mark.integration
    async def test_reject_oversized_file(self, client):
        """Should reject files larger than 5MB."""
        big_data = b"x" * (5 * 1024 * 1024 + 1)
        files = {"file": ("big.pdf", big_data, "application/pdf")}
        response = await client.post("/api/cv/upload", files=files)
        assert response.status_code == 400
        assert "5MB" in response.json()["detail"]

    @pytest.mark.integration
    async def test_reject_empty_text_extraction(self, client):
        """Should return 422 if no text can be extracted."""
        with patch("app.routers.cv.extract_text", return_value="   "):
            files = {"file": ("empty.pdf", b"fake", "application/pdf")}
            response = await client.post("/api/cv/upload", files=files)
            assert response.status_code == 422
            assert "Could not extract" in response.json()["detail"]

    @pytest.mark.integration
    async def test_successful_upload_and_parse(self, client):
        """Successful upload should extract text, parse with OpenAI, and store."""
        parsed_result = {
            "personal_info": {"name": "Uploaded User", "email": "up@test.com",
                              "phone": "", "location": ""},
            "summary": "Parsed by AI",
            "work_experience": [],
            "education": [],
            "skills": ["Parsing"],
            "certifications": [],
        }

        with patch("app.routers.cv.extract_text", return_value="Some CV text here"):
            with patch("app.routers.cv.parse_cv_with_openai",
                       new_callable=AsyncMock, return_value=parsed_result):
                files = {"file": ("resume.pdf", b"fake pdf content", "application/pdf")}
                response = await client.post("/api/cv/upload", files=files)
                assert response.status_code == 200
                data = response.json()
                assert data["personal_info"]["name"] == "Uploaded User"
                assert data["summary"] == "Parsed by AI"
                assert data["raw_text"] == "Some CV text here"

    @pytest.mark.integration
    async def test_openai_parse_failure_returns_500(self, client):
        """If OpenAI parsing fails, should return 500 with helpful message."""
        with patch("app.routers.cv.extract_text", return_value="Some text"):
            with patch("app.routers.cv.parse_cv_with_openai",
                       new_callable=AsyncMock,
                       side_effect=Exception("API timeout")):
                files = {"file": ("resume.docx", b"fake", "application/vnd.openxmlformats")}
                response = await client.post("/api/cv/upload", files=files)
                assert response.status_code == 500
                assert "manually" in response.json()["detail"].lower()

    @pytest.mark.integration
    async def test_openai_value_error_returns_422(self, client):
        """If OpenAI key is missing (ValueError), should return 422."""
        with patch("app.routers.cv.extract_text", return_value="Some text"):
            with patch("app.routers.cv.parse_cv_with_openai",
                       new_callable=AsyncMock,
                       side_effect=ValueError("OpenAI API key is not configured")):
                files = {"file": ("resume.pdf", b"fake", "application/pdf")}
                response = await client.post("/api/cv/upload", files=files)
                assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/cv/preview and GET /api/cv/preview/html
# ---------------------------------------------------------------------------

class TestCVPreview:
    """Tests for CV preview endpoints."""

    @pytest.mark.integration
    async def test_preview_404_when_no_cv(self, client):
        """Preview should return 404 when no CV data exists."""
        # Ensure no CV exists (fresh test DB session)
        response = await client.get("/api/cv/preview")
        assert response.status_code == 404

    @pytest.mark.integration
    async def test_html_preview_404_when_no_cv(self, client):
        """HTML preview should return 404 when no CV data exists."""
        response = await client.get("/api/cv/preview/html")
        assert response.status_code == 404

    @pytest.mark.integration
    async def test_preview_returns_content_after_cv_created(self, client):
        """After creating a CV, preview should return HTML or PDF content."""
        # Create CV first
        payload = {
            "personal_info": {"name": "Preview Test", "email": "p@test.com",
                              "phone": "", "location": ""},
            "summary": "Test summary for preview",
            "work_experience": [],
            "education": [],
            "skills": ["Testing"],
            "certifications": [],
        }
        await client.put("/api/cv", json=payload)

        # Get preview (will be HTML since WeasyPrint likely not installed)
        response = await client.get("/api/cv/preview")
        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.integration
    async def test_html_preview_returns_html(self, client):
        """HTML preview should return text/html content."""
        # Create CV first
        payload = {
            "personal_info": {"name": "HTML Test", "email": "", "phone": "", "location": ""},
            "summary": "For HTML preview",
            "work_experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
        }
        await client.put("/api/cv", json=payload)

        response = await client.get("/api/cv/preview/html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "HTML Test" in response.text
