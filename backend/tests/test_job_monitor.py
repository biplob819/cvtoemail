"""Unit tests for job_monitor.py -- Celery tasks and job monitoring logic.

Tests cover:
- Job monitoring task execution
- Job deduplication logic
- Description fetching
- Error handling and retries
- Source processing
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_fetch_job_description_success():
    """Test successful job description fetching."""
    from app.tasks.job_monitor import fetch_job_description
    
    mock_html = """
    <html>
        <body>
            <div class="description">
                <h2>About the Role</h2>
                <p>We are seeking a talented engineer...</p>
                <h3>Requirements</h3>
                <ul>
                    <li>5+ years of experience</li>
                    <li>Python expertise</li>
                </ul>
            </div>
        </body>
    </html>
    """
    
    with patch("app.tasks.job_monitor.httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        description = await fetch_job_description("https://example.com/job/123")
        
        assert "About the Role" in description
        assert "5+ years of experience" in description
        assert len(description) > 50


@pytest.mark.asyncio
async def test_fetch_job_description_failure():
    """Test job description fetching handles errors gracefully."""
    from app.tasks.job_monitor import fetch_job_description
    
    with patch("app.tasks.job_monitor.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Network error")
        )
        
        description = await fetch_job_description("https://example.com/job/123")
        
        # Should return empty string on error, not raise
        assert description == ""


@pytest.mark.asyncio
async def test_fetch_job_description_truncation():
    """Test that very long descriptions are truncated."""
    from app.tasks.job_monitor import fetch_job_description
    
    # Create a very long description (>10000 chars)
    long_content = "A" * 15000
    mock_html = f"<html><body><div class='description'>{long_content}</div></body></html>"
    
    with patch("app.tasks.job_monitor.httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        description = await fetch_job_description("https://example.com/job/123")
        
        # Should be truncated to ~10000 chars
        assert len(description) <= 10010  # 10000 + "..."
        assert description.endswith("...")


@pytest.mark.asyncio
async def test_process_source_success(test_db):
    """Test successful source processing with new jobs."""
    from app.tasks.job_monitor import process_source
    from app.models.job_source import JobSource
    from app.models.job import Job
    from app.database import Base
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    # Use an isolated in-memory sync SQLite so process_source sees our test data
    sync_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(sync_engine)
    TestSyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)

    # Insert the source into the sync engine so last_checked can be updated
    with TestSyncSession() as db:
        source = JobSource(
            id=1,
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        db.commit()

    # Mock scraper to return job listings
    mock_jobs = [
        {
            "title": "Software Engineer",
            "company": "Example Corp",
            "location": "San Francisco",
            "url": "https://example.com/jobs/1",
            "description": "",
        },
        {
            "title": "Product Manager",
            "company": "Example Corp",
            "location": "Remote",
            "url": "https://example.com/jobs/2",
            "description": "",
        },
    ]

    with patch("app.tasks.job_monitor.SyncSession", TestSyncSession):
        with patch("app.tasks.job_monitor.scrape_source", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_jobs

            with patch("app.tasks.job_monitor.fetch_job_description", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = "Job description here"

                result = await process_source(1, "https://example.com/jobs", "Example Corp")

    # Verify result
    assert result["jobs_found"] == 2
    assert result["new_jobs"] == 2
    assert result["errors"] == []

    # Verify jobs were stored (using the same isolated sync engine)
    with TestSyncSession() as session:
        jobs = session.execute(select(Job)).scalars().all()
        assert len(jobs) == 2
        titles = {j.title for j in jobs}
        assert "Software Engineer" in titles
        assert "Product Manager" in titles
        for job in jobs:
            assert job.status == "New"
            assert job.is_new == True


@pytest.mark.asyncio
async def test_process_source_deduplication(test_db):
    """Test that duplicate jobs (by URL) are not re-added."""
    from app.tasks.job_monitor import process_source
    from app.models.job_source import JobSource
    from app.models.job import Job
    from app.database import Base
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    # Use an isolated in-memory sync SQLite so process_source sees our test data
    sync_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(sync_engine)
    TestSyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)

    # Insert source and existing job directly into the sync engine
    with TestSyncSession() as db:
        source = JobSource(
            id=1,
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        db.commit()

        existing_job = Job(
            source_id=1,
            title="Existing Job",
            company="Example Corp",
            location="Remote",
            url="https://example.com/jobs/existing",
            status="Viewed",
        )
        db.add(existing_job)
        db.commit()

    # Mock scraper to return one existing and one new job
    mock_jobs = [
        {
            "title": "Existing Job",
            "company": "Example Corp",
            "location": "Remote",
            "url": "https://example.com/jobs/existing",  # Duplicate!
            "description": "",
        },
        {
            "title": "New Job",
            "company": "Example Corp",
            "location": "San Francisco",
            "url": "https://example.com/jobs/new",
            "description": "",
        },
    ]

    with patch("app.tasks.job_monitor.SyncSession", TestSyncSession):
        with patch("app.tasks.job_monitor.scrape_source", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_jobs

            with patch("app.tasks.job_monitor.fetch_job_description", new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = "Job description"

                result = await process_source(1, "https://example.com/jobs", "Example Corp")

    # Verify result
    assert result["jobs_found"] == 2
    assert result["new_jobs"] == 1  # Only one new job added

    # Verify only one new job was added (using the same sync engine)
    with TestSyncSession() as db:
        jobs = db.execute(select(Job)).scalars().all()
        assert len(jobs) == 2  # 1 existing + 1 new
        new_jobs = [j for j in jobs if j.title == "New Job"]
        assert len(new_jobs) == 1


@pytest.mark.asyncio
async def test_process_source_error_handling(test_db):
    """Test that source processing handles errors gracefully."""
    from app.tasks.job_monitor import process_source
    from app.models.job_source import JobSource
    
    # Create test source
    async with test_db() as db:
        source = JobSource(
            id=1,
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
        )
        db.add(source)
        await db.commit()
    
    # Mock scraper to raise an error
    with patch("app.tasks.job_monitor.scrape_source", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.side_effect = Exception("Scraping failed")
        
        result = await process_source(1, "https://example.com/jobs", "Example Corp")
    
    # Verify error was caught and logged
    assert result["jobs_found"] == 0
    assert result["new_jobs"] == 0
    assert len(result["errors"]) > 0
    assert "Scraping failed" in str(result["errors"])


@pytest.mark.asyncio
async def test_process_source_updates_last_checked(test_db):
    """Test that last_checked timestamp is updated after processing."""
    from app.tasks.job_monitor import process_source
    from app.models.job_source import JobSource
    from app.database import Base
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    # Use an isolated in-memory sync SQLite so process_source sees our test data
    sync_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(sync_engine)
    TestSyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)

    # Insert source directly into the sync engine
    with TestSyncSession() as db:
        source = JobSource(
            id=1,
            url="https://example.com/jobs",
            portal_name="Example Corp",
            is_active=True,
            last_checked=None,
        )
        db.add(source)
        db.commit()

    # Mock scraper to return empty list — last_checked should still be updated
    with patch("app.tasks.job_monitor.SyncSession", TestSyncSession):
        with patch("app.tasks.job_monitor.scrape_source", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = []

            await process_source(1, "https://example.com/jobs", "Example Corp")

    # Verify last_checked was updated (using the same sync engine)
    with TestSyncSession() as db:
        stmt = select(JobSource).where(JobSource.id == 1)
        source = db.execute(stmt).scalar_one()
        assert source.last_checked is not None


def test_monitor_all_sources_no_active_sources(test_db):
    """Test monitor_all_sources when there are no active sources."""
    from app.tasks.job_monitor import monitor_all_sources
    
    # Mock the SyncSession to return no active sources
    with patch("app.tasks.job_monitor.SyncSession") as mock_session:
        mock_db = Mock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = None
        
        result = monitor_all_sources()
    
    assert result["status"] == "completed"
    assert result["sources_processed"] == 0
    assert result["total_jobs_found"] == 0
    assert result["total_new_jobs"] == 0


def test_test_task():
    """Test the simple test_task executes successfully."""
    from app.tasks.job_monitor import test_task
    
    result = test_task()
    
    assert result["status"] == "success"
    assert "message" in result
