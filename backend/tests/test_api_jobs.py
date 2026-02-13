"""Integration tests for job API endpoints.

Tests cover:
- GET /api/jobs (list with filters)
- GET /api/jobs/stats (statistics)
- GET /api/jobs/:id (single job, marks as viewed)
- PUT /api/jobs/:id (update status)
- POST /api/jobs/bulk-skip (bulk skip)
- POST /api/jobs/:id/generate-cv (placeholder for M4)
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_list_jobs_empty(client: AsyncClient, test_db):
    """Test listing jobs when database is empty."""
    response = await client.get("/api/jobs")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_jobs_with_data(client: AsyncClient, test_db):
    """Test listing jobs with data."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    # Create test data
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job1 = Job(
            source_id=source.id,
            title="Software Engineer",
            company="Example Corp",
            location="San Francisco",
            url="https://example.com/jobs/1",
            status="New",
            is_new=True,
        )
        job2 = Job(
            source_id=source.id,
            title="Product Manager",
            company="Example Corp",
            location="Remote",
            url="https://example.com/jobs/2",
            status="Viewed",
            is_new=False,
        )
        db.add(job1)
        db.add(job2)
        await db.commit()
    
    # List all jobs
    response = await client.get("/api/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2
    assert jobs[0]["title"] in ["Software Engineer", "Product Manager"]
    assert jobs[0]["source_name"] == "Example Corp"


@pytest.mark.asyncio
async def test_list_jobs_filter_by_source(client: AsyncClient, test_db):
    """Test filtering jobs by source_id."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    # Create two sources with jobs
    async with test_db() as db:
        source1 = JobSource(
            url="https://example1.com/jobs",
            portal_name="Company A",
            is_active=True,
        )
        source2 = JobSource(
            url="https://example2.com/jobs",
            portal_name="Company B",
            is_active=True,
        )
        db.add(source1)
        db.add(source2)
        await db.commit()
        await db.refresh(source1)
        await db.refresh(source2)
        
        job1 = Job(
            source_id=source1.id,
            title="Job from A",
            url="https://example1.com/jobs/1",
            status="New",
        )
        job2 = Job(
            source_id=source2.id,
            title="Job from B",
            url="https://example2.com/jobs/1",
            status="New",
        )
        db.add(job1)
        db.add(job2)
        await db.commit()
    
    # Filter by source 1
    response = await client.get(f"/api/jobs?source_id={source1.id}")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Job from A"


@pytest.mark.asyncio
async def test_list_jobs_filter_by_status(client: AsyncClient, test_db):
    """Test filtering jobs by status."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job1 = Job(
            source_id=source.id,
            title="New Job",
            url="https://example.com/jobs/1",
            status="New",
        )
        job2 = Job(
            source_id=source.id,
            title="Viewed Job",
            url="https://example.com/jobs/2",
            status="Viewed",
        )
        job3 = Job(
            source_id=source.id,
            title="Skipped Job",
            url="https://example.com/jobs/3",
            status="Skipped",
        )
        db.add_all([job1, job2, job3])
        await db.commit()
    
    # Filter by "New" status
    response = await client.get("/api/jobs?status=New")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "New Job"
    
    # Filter by "Skipped" status
    response = await client.get("/api/jobs?status=Skipped")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Skipped Job"


@pytest.mark.asyncio
async def test_list_jobs_pagination(client: AsyncClient, test_db):
    """Test pagination with limit and offset."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        # Create 5 jobs
        for i in range(5):
            job = Job(
                source_id=source.id,
                title=f"Job {i+1}",
                url=f"https://example.com/jobs/{i+1}",
                status="New",
            )
            db.add(job)
        await db.commit()
    
    # Get first 2 jobs
    response = await client.get("/api/jobs?limit=2&offset=0")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2
    
    # Get next 2 jobs
    response = await client.get("/api/jobs?limit=2&offset=2")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2


@pytest.mark.asyncio
async def test_get_job_stats(client: AsyncClient, test_db):
    """Test getting job statistics."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    now = datetime.utcnow()
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        # Create jobs with different statuses and dates
        job1 = Job(
            source_id=source.id,
            title="Recent New Job",
            url="https://example.com/jobs/1",
            status="New",
            discovered_at=now,
        )
        job2 = Job(
            source_id=source.id,
            title="Old Viewed Job",
            url="https://example.com/jobs/2",
            status="Viewed",
            discovered_at=now - timedelta(days=10),
        )
        job3 = Job(
            source_id=source.id,
            title="Recent Skipped Job",
            url="https://example.com/jobs/3",
            status="Skipped",
            discovered_at=now - timedelta(hours=12),
        )
        db.add_all([job1, job2, job3])
        await db.commit()
    
    response = await client.get("/api/jobs/stats")
    assert response.status_code == 200
    stats = response.json()
    
    assert stats["total_jobs"] == 3
    assert stats["new_jobs_24h"] == 2  # job1 and job3
    assert stats["new_jobs_7d"] == 2   # job1 and job3
    assert stats["by_status"]["New"] == 1
    assert stats["by_status"]["Viewed"] == 1
    assert stats["by_status"]["Skipped"] == 1


@pytest.mark.asyncio
async def test_get_job_by_id(client: AsyncClient, test_db):
    """Test getting a single job by ID."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            company="Example Corp",
            location="Remote",
            description="Full job description here",
            url="https://example.com/jobs/1",
            status="New",
            is_new=True,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    response = await client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["title"] == "Test Job"
    assert job_data["source_name"] == "Example Corp"
    assert job_data["description"] == "Full job description here"


@pytest.mark.asyncio
async def test_get_job_marks_as_viewed(client: AsyncClient, test_db):
    """Test that getting a job marks it as viewed if it was new."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    from sqlalchemy import select
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="New Job",
            url="https://example.com/jobs/1",
            status="New",
            is_new=True,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    # Get the job
    response = await client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["status"] == "Viewed"
    assert job_data["is_new"] == False
    
    # Verify in database
    async with test_db() as db:
        stmt = select(Job).where(Job.id == job_id)
        job = (await db.execute(stmt)).scalar_one()
        assert job.status == "Viewed"
        assert job.is_new == False


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient, test_db):
    """Test getting a non-existent job returns 404."""
    response = await client.get("/api/jobs/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_job_status(client: AsyncClient, test_db):
    """Test updating a job's status."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            url="https://example.com/jobs/1",
            status="New",
            is_new=True,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    # Update status to Skipped
    response = await client.put(
        f"/api/jobs/{job_id}",
        json={"status": "Skipped", "is_new": False}
    )
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["status"] == "Skipped"
    assert job_data["is_new"] == False


@pytest.mark.asyncio
async def test_update_job_invalid_status(client: AsyncClient, test_db):
    """Test that invalid status values are rejected."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            url="https://example.com/jobs/1",
            status="New",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    # Try to update with invalid status
    response = await client.put(
        f"/api/jobs/{job_id}",
        json={"status": "InvalidStatus"}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_bulk_skip_jobs(client: AsyncClient, test_db):
    """Test bulk skipping multiple jobs."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    from sqlalchemy import select
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job1 = Job(
            source_id=source.id,
            title="Job 1",
            url="https://example.com/jobs/1",
            status="New",
        )
        job2 = Job(
            source_id=source.id,
            title="Job 2",
            url="https://example.com/jobs/2",
            status="New",
        )
        job3 = Job(
            source_id=source.id,
            title="Job 3",
            url="https://example.com/jobs/3",
            status="Viewed",
        )
        db.add_all([job1, job2, job3])
        await db.commit()
        await db.refresh(job1)
        await db.refresh(job2)
        await db.refresh(job3)
        job_ids = [job1.id, job2.id, job3.id]
    
    # Bulk skip
    response = await client.post(
        "/api/jobs/bulk-skip",
        json={"job_ids": job_ids}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["updated_count"] == 3
    
    # Verify all jobs are skipped
    async with test_db() as db:
        stmt = select(Job).where(Job.id.in_(job_ids))
        jobs = (await db.execute(stmt)).scalars().all()
        for job in jobs:
            assert job.status == "Skipped"
            assert job.is_new == False


@pytest.mark.asyncio
async def test_bulk_skip_empty_list(client: AsyncClient, test_db):
    """Test that bulk skip with empty list fails."""
    response = await client.post(
        "/api/jobs/bulk-skip",
        json={"job_ids": []}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_generate_cv_success(client: AsyncClient, test_db):
    """Test successful CV generation for a job."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    from app.models.cv import CVProfile
    from unittest.mock import patch, AsyncMock, MagicMock
    import json
    
    # Create CV profile
    async with test_db() as db:
        cv_profile = CVProfile(
            personal_info={"name": "Jane Doe", "email": "jane@example.com"},
            summary="Experienced engineer",
            work_experience=[{
                "title": "Engineer",
                "company": "TechCorp",
                "duration": "2021-Present",
                "achievements": ["Built APIs"]
            }],
            education=[],
            skills=["Python", "FastAPI"],
            certifications=[],
        )
        db.add(cv_profile)
        await db.commit()
    
    # Create job with description
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Senior Engineer",
            company="TechStartup",
            url="https://example.com/jobs/1",
            description="We need a senior engineer with Python and FastAPI experience. " * 5,  # Make it long enough
            status="New",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    # Mock the CV tailoring
    tailored_cv = {
        "personal_info": {"name": "Jane Doe", "email": "jane@example.com"},
        "summary": "Experienced engineer",
        "work_experience": [],
        "education": [],
        "skills": ["Python", "FastAPI"],
        "certifications": [],
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(tailored_cv)
    
    with patch("app.routers.jobs.tailor_cv_for_job", new_callable=AsyncMock) as mock_tailor:
        with patch("app.routers.jobs.generate_cv_pdf") as mock_pdf:
            mock_tailor.return_value = tailored_cv
            mock_pdf.return_value = b"PDF content"
            
            response = await client.post(f"/api/jobs/{job_id}/generate-cv")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "cv_path" in result
            assert "filename" in result
            
            # Verify job was updated
            async with test_db() as db:
                from sqlalchemy import select
                stmt = select(Job).where(Job.id == job_id)
                result = await db.execute(stmt)
                updated_job = result.scalar_one()
                assert updated_job.status == "CV Generated"
                assert updated_job.cv_pdf_path is not None
                assert updated_job.cv_generated_at is not None


@pytest.mark.asyncio
async def test_generate_cv_job_not_found(client: AsyncClient, test_db):
    """Test generate CV with non-existent job returns 404."""
    response = await client.post("/api/jobs/99999/generate-cv")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_cv_no_cv_profile(client: AsyncClient, test_db):
    """Test generate CV fails when no CV profile exists."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            url="https://example.com/jobs/1",
            description="Test description",
            status="New",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    response = await client.post(f"/api/jobs/{job_id}/generate-cv")
    assert response.status_code == 400
    assert "No CV profile found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_cv_description_too_short(client: AsyncClient, test_db):
    """Test generate CV fails when job description is too short."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    from app.models.cv import CVProfile
    
    # Create CV profile
    async with test_db() as db:
        cv_profile = CVProfile(
            personal_info={"name": "Jane Doe", "email": "jane@example.com"},
            summary="Experienced engineer",
            work_experience=[],
            education=[],
            skills=["Python"],
            certifications=[],
        )
        db.add(cv_profile)
        await db.commit()
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            url="https://example.com/jobs/1",
            description="Too short",  # Less than 50 chars
            status="New",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    response = await client.post(f"/api/jobs/{job_id}/generate-cv")
    assert response.status_code == 400
    assert "too short or missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_cv_success(client: AsyncClient, test_db):
    """Test successful CV download."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    from pathlib import Path
    import tempfile
    import os
    
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(b"PDF content")
        pdf_path = tmp.name
    
    try:
        async with test_db() as db:
            source = JobSource(
                url="https://example.com/jobs",
                portal_name="Example Corp",
                is_active=True,
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
            
            job = Job(
                source_id=source.id,
                title="Software Engineer",
                company="TechCorp",
                url="https://example.com/jobs/1",
                status="CV Generated",
                cv_pdf_path=pdf_path,
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            job_id = job.id
        
        response = await client.get(f"/api/jobs/{job_id}/cv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert b"PDF content" in response.content
    finally:
        # Clean up temp file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


@pytest.mark.asyncio
async def test_download_cv_job_not_found(client: AsyncClient, test_db):
    """Test download CV with non-existent job returns 404."""
    response = await client.get("/api/jobs/99999/cv")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_cv_not_generated(client: AsyncClient, test_db):
    """Test download CV when CV hasn't been generated yet."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            url="https://example.com/jobs/1",
            status="New",
            cv_pdf_path=None,  # No CV generated
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    response = await client.get(f"/api/jobs/{job_id}/cv")
    assert response.status_code == 404
    assert "No CV has been generated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_cv_file_missing(client: AsyncClient, test_db):
    """Test download CV when PDF file is missing from disk."""
    from app.models.job_source import JobSource
    from app.models.job import Job
    
    async with test_db() as db:
        source = JobSource(
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        
        job = Job(
            source_id=source.id,
            title="Test Job",
            url="https://example.com/jobs/1",
            status="CV Generated",
            cv_pdf_path="/nonexistent/path/cv.pdf",  # File doesn't exist
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id
    
    response = await client.get(f"/api/jobs/{job_id}/cv")
    assert response.status_code == 404
    assert "not found on disk" in response.json()["detail"]
