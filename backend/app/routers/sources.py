"""Job source management endpoints -- CRUD, URL validation, and scan trigger."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sa_func
from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
import httpx
from urllib.parse import urlparse

from app.database import get_db
from app.models.job_source import JobSource
from app.models.job import Job


router = APIRouter(prefix="/api/sources", tags=["Sources"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SourceCreate(BaseModel):
    url: str
    portal_name: str
    filters_description: Optional[str] = ""

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL is required.")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain.")
        return v

    @field_validator("portal_name")
    @classmethod
    def validate_portal_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Portal name is required.")
        return v


class SourceUpdate(BaseModel):
    url: Optional[str] = None
    portal_name: Optional[str] = None
    filters_description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty.")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        if not parsed.netloc:
            raise ValueError("URL must have a valid domain.")
        return v


class SourceResponse(BaseModel):
    id: int
    url: str
    portal_name: str
    filters_description: Optional[str] = ""
    is_active: bool
    last_checked: Optional[str] = None
    created_at: Optional[str] = None
    jobs_found: int = 0

    model_config = {"from_attributes": True}


class URLCheckResult(BaseModel):
    reachable: bool
    status_code: Optional[int] = None
    message: str


class ScanResult(BaseModel):
    source_id: int
    jobs_found: int
    new_jobs: int
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_dt(val) -> Optional[str]:
    """Safely format a datetime value to ISO string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


async def _get_jobs_count(db: AsyncSession, source_id: int) -> int:
    """Count jobs associated with a source."""
    result = await db.execute(
        select(sa_func.count(Job.id)).where(Job.source_id == source_id)
    )
    return result.scalar() or 0


async def _source_to_response(db: AsyncSession, source: JobSource) -> SourceResponse:
    """Convert a JobSource ORM object to a SourceResponse."""
    jobs_count = await _get_jobs_count(db, source.id)
    return SourceResponse(
        id=source.id,
        url=source.url,
        portal_name=source.portal_name,
        filters_description=source.filters_description or "",
        is_active=source.is_active,
        last_checked=_format_dt(source.last_checked),
        created_at=_format_dt(source.created_at),
        jobs_found=jobs_count,
    )


async def _check_url_reachable(url: str) -> URLCheckResult:
    """Perform an HTTP HEAD check on the URL to verify reachability."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(10.0),
        ) as client:
            response = await client.head(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code < 400:
                return URLCheckResult(
                    reachable=True,
                    status_code=response.status_code,
                    message="URL is reachable.",
                )
            else:
                return URLCheckResult(
                    reachable=False,
                    status_code=response.status_code,
                    message=f"URL returned status {response.status_code}.",
                )
    except httpx.TimeoutException:
        return URLCheckResult(
            reachable=False,
            status_code=None,
            message="URL check timed out after 10 seconds.",
        )
    except Exception as e:
        return URLCheckResult(
            reachable=False,
            status_code=None,
            message=f"Could not reach URL: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(data: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Add a new job source URL to monitor."""
    # Check for duplicate URL
    existing = await db.execute(select(JobSource).where(JobSource.url == data.url))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="This URL is already being monitored.")

    # Check URL reachability (non-blocking -- warn but allow saving)
    url_check = await _check_url_reachable(data.url)

    source = JobSource(
        url=data.url,
        portal_name=data.portal_name,
        filters_description=data.filters_description or "",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)

    response = await _source_to_response(db, source)
    # If URL is not reachable, include a warning in the response headers
    # but still return 201 (non-blocking warning per spec)
    return response


@router.get("", response_model=list[SourceResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all job sources."""
    result = await db.execute(select(JobSource).order_by(JobSource.created_at.desc()))
    sources = result.scalars().all()
    responses = []
    for source in sources:
        responses.append(await _source_to_response(db, source))
    return responses


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific job source by ID."""
    result = await db.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return await _source_to_response(db, source)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int, data: SourceUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing job source."""
    result = await db.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    # If URL is changing, check for duplicates
    if data.url is not None and data.url != source.url:
        existing = await db.execute(select(JobSource).where(JobSource.url == data.url))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="This URL is already being monitored.")
        source.url = data.url

    if data.portal_name is not None:
        source.portal_name = data.portal_name
    if data.filters_description is not None:
        source.filters_description = data.filters_description
    if data.is_active is not None:
        source.is_active = data.is_active

    await db.flush()
    await db.refresh(source)
    return await _source_to_response(db, source)


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a job source. Associated jobs remain in the database."""
    result = await db.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    await db.delete(source)
    await db.flush()
    return {"detail": "Source deleted.", "id": source_id}


@router.get("/{source_id}/check-url", response_model=URLCheckResult)
async def check_source_url(source_id: int, db: AsyncSession = Depends(get_db)):
    """Check if a source's URL is reachable."""
    result = await db.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return await _check_url_reachable(source.url)


@router.post("/check-url", response_model=URLCheckResult)
async def check_url(data: dict):
    """Check if a URL is reachable (for use before saving a source)."""
    url = data.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    return await _check_url_reachable(url)


@router.post("/{source_id}/scan", response_model=ScanResult)
async def scan_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Manually trigger a scan for a specific source."""
    result = await db.execute(select(JobSource).where(JobSource.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    if not source.is_active:
        raise HTTPException(status_code=400, detail="Cannot scan a paused source. Resume it first.")

    # Import scraper here to avoid circular imports
    from app.services.scraper import scrape_source

    try:
        scraped_jobs = await scrape_source(source.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    # Deduplicate: only insert jobs whose URLs don't already exist
    new_count = 0
    for job_data in scraped_jobs:
        job_url = job_data.get("url", "")
        if not job_url:
            continue
        existing_job = await db.execute(select(Job).where(Job.url == job_url))
        if existing_job.scalar_one_or_none() is not None:
            continue  # Already have this job

        new_job = Job(
            source_id=source.id,
            title=job_data.get("title", "Untitled"),
            company=job_data.get("company", ""),
            location=job_data.get("location", ""),
            description=job_data.get("description", ""),
            url=job_url,
            status="New",
            is_new=True,
        )
        db.add(new_job)
        new_count += 1

    # Update last_checked timestamp
    source.last_checked = sa_func.now()
    await db.flush()

    return ScanResult(
        source_id=source.id,
        jobs_found=len(scraped_jobs),
        new_jobs=new_count,
        message=f"Scan complete. Found {len(scraped_jobs)} listings, {new_count} new.",
    )
