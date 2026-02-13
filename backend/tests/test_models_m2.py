"""Unit tests for Milestone 2 database models -- JobSource and Job."""

import pytest
from sqlalchemy import select

from app.models.job_source import JobSource
from app.models.job import Job


class TestJobSourceModel:
    """Tests for the JobSource database model."""

    @pytest.mark.integration
    async def test_create_job_source(self, db_session):
        """Should create a JobSource with all fields."""
        source = JobSource(
            url="https://example.com/careers",
            portal_name="Example Corp",
            filters_description="Remote only",
        )
        db_session.add(source)
        await db_session.flush()

        assert source.id is not None
        assert source.url == "https://example.com/careers"
        assert source.portal_name == "Example Corp"
        assert source.filters_description == "Remote only"
        assert source.is_active is True
        assert source.last_checked is None

    @pytest.mark.integration
    async def test_job_source_defaults(self, db_session):
        """JobSource should have sensible defaults."""
        source = JobSource(
            url="https://test.com/jobs",
            portal_name="Test Co",
        )
        db_session.add(source)
        await db_session.flush()

        assert source.is_active is True
        assert source.last_checked is None
        assert source.filters_description in (None, "")

    @pytest.mark.integration
    async def test_job_source_unique_url(self, db_session):
        """JobSource URLs must be unique."""
        source1 = JobSource(url="https://unique.com/jobs", portal_name="Source 1")
        db_session.add(source1)
        await db_session.flush()

        source2 = JobSource(url="https://unique.com/jobs", portal_name="Source 2")
        db_session.add(source2)

        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    @pytest.mark.integration
    async def test_job_source_update(self, db_session):
        """Should be able to update JobSource fields."""
        source = JobSource(
            url="https://update-test.com/careers",
            portal_name="Old Name",
            is_active=True,
        )
        db_session.add(source)
        await db_session.flush()

        source.portal_name = "New Name"
        source.is_active = False
        await db_session.flush()

        result = await db_session.execute(
            select(JobSource).where(JobSource.id == source.id)
        )
        loaded = result.scalar_one()
        assert loaded.portal_name == "New Name"
        assert loaded.is_active is False

    @pytest.mark.integration
    async def test_job_source_query_active(self, db_session):
        """Should be able to query only active sources."""
        active = JobSource(
            url="https://active-src.com/jobs",
            portal_name="Active",
            is_active=True,
        )
        paused = JobSource(
            url="https://paused-src.com/jobs",
            portal_name="Paused",
            is_active=False,
        )
        db_session.add_all([active, paused])
        await db_session.flush()

        result = await db_session.execute(
            select(JobSource).where(JobSource.is_active == True)  # noqa: E712
        )
        active_sources = result.scalars().all()
        urls = [s.url for s in active_sources]
        assert "https://active-src.com/jobs" in urls


class TestJobModel:
    """Tests for the Job database model."""

    @pytest.mark.integration
    async def test_create_job(self, db_session):
        """Should create a Job with all fields."""
        source = JobSource(
            url="https://job-test.com/careers",
            portal_name="Test Portal",
        )
        db_session.add(source)
        await db_session.flush()

        job = Job(
            source_id=source.id,
            title="Senior Developer",
            company="TechCo",
            location="Remote",
            description="A great role for experienced developers.",
            url="https://job-test.com/careers/123",
            status="New",
            is_new=True,
        )
        db_session.add(job)
        await db_session.flush()

        assert job.id is not None
        assert job.source_id == source.id
        assert job.title == "Senior Developer"
        assert job.status == "New"
        assert job.is_new is True

    @pytest.mark.integration
    async def test_job_defaults(self, db_session):
        """Job should have sensible defaults."""
        source = JobSource(
            url="https://job-defaults.com/careers",
            portal_name="Defaults Portal",
        )
        db_session.add(source)
        await db_session.flush()

        job = Job(
            source_id=source.id,
            title="Any Role",
            url="https://job-defaults.com/careers/456",
        )
        db_session.add(job)
        await db_session.flush()

        assert job.status == "New"
        assert job.is_new is True
        assert job.company in (None, "")
        assert job.location in (None, "")

    @pytest.mark.integration
    async def test_job_unique_url(self, db_session):
        """Job URLs must be unique (deduplication key)."""
        source = JobSource(
            url="https://job-unique.com/careers",
            portal_name="Unique Portal",
        )
        db_session.add(source)
        await db_session.flush()

        job1 = Job(
            source_id=source.id,
            title="Role A",
            url="https://job-unique.com/careers/789",
        )
        db_session.add(job1)
        await db_session.flush()

        job2 = Job(
            source_id=source.id,
            title="Role B",
            url="https://job-unique.com/careers/789",
        )
        db_session.add(job2)

        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    @pytest.mark.integration
    async def test_job_status_update(self, db_session):
        """Should be able to update job status through the lifecycle."""
        source = JobSource(
            url="https://job-status.com/careers",
            portal_name="Status Portal",
        )
        db_session.add(source)
        await db_session.flush()

        job = Job(
            source_id=source.id,
            title="Status Test",
            url="https://job-status.com/careers/status1",
        )
        db_session.add(job)
        await db_session.flush()

        assert job.status == "New"

        job.status = "Viewed"
        job.is_new = False
        await db_session.flush()

        result = await db_session.execute(select(Job).where(Job.id == job.id))
        loaded = result.scalar_one()
        assert loaded.status == "Viewed"
        assert loaded.is_new is False

    @pytest.mark.integration
    async def test_job_query_by_source(self, db_session):
        """Should be able to query jobs by source_id."""
        source = JobSource(
            url="https://job-query.com/careers",
            portal_name="Query Portal",
        )
        db_session.add(source)
        await db_session.flush()

        for i in range(3):
            job = Job(
                source_id=source.id,
                title=f"Job {i}",
                url=f"https://job-query.com/careers/{i}",
            )
            db_session.add(job)
        await db_session.flush()

        result = await db_session.execute(
            select(Job).where(Job.source_id == source.id)
        )
        jobs = result.scalars().all()
        assert len(jobs) == 3
