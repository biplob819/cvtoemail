"""API router for job management."""

from datetime import datetime, timedelta
from typing import Optional, List
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.job import Job
from app.models.job_source import JobSource
from app.models.cv import CVProfile
from app.services.cv_writer import tailor_cv_for_job
from app.services.pdf_generator import generate_cv_pdf
from app.config import settings

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ============================================================================
# Pydantic Models
# ============================================================================

class JobResponse(BaseModel):
    """Job response model."""
    id: int
    source_id: int
    source_name: Optional[str] = None
    title: str
    company: str
    location: str
    description: str
    url: str
    status: str
    is_new: bool
    discovered_at: datetime

    model_config = {"from_attributes": True}


class JobUpdateRequest(BaseModel):
    """Job update request model."""
    status: Optional[str] = Field(None, pattern="^(New|Viewed|CV Generated|CV Sent|Skipped)$")
    is_new: Optional[bool] = None


class BulkSkipRequest(BaseModel):
    """Bulk skip request model."""
    job_ids: List[int] = Field(..., min_items=1)


class JobStatsResponse(BaseModel):
    """Job statistics response."""
    total_jobs: int
    new_jobs_24h: int
    new_jobs_7d: int
    by_status: dict


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    status: Optional[str] = Query(None, description="Filter by status (New/Viewed/CV Sent/Skipped)"),
    date_from: Optional[datetime] = Query(None, description="Filter jobs discovered after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter jobs discovered before this date"),
    limit: int = Query(100, ge=1, le=500, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with optional filters.
    
    Supports filtering by:
    - source_id: Show jobs from a specific source
    - status: Filter by job status (New/Viewed/CV Generated/CV Sent/Skipped)
    - date_from/date_to: Date range filter
    - limit/offset: Pagination
    
    Results are ordered by discovered_at DESC (newest first).
    """
    # Build the query
    stmt = select(Job, JobSource.portal_name).join(
        JobSource, Job.source_id == JobSource.id
    )
    
    # Apply filters
    conditions = []
    if source_id:
        conditions.append(Job.source_id == source_id)
    if status:
        conditions.append(Job.status == status)
    if date_from:
        conditions.append(Job.discovered_at >= date_from)
    if date_to:
        conditions.append(Job.discovered_at <= date_to)
    
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    # Order by newest first
    stmt = stmt.order_by(Job.discovered_at.desc())
    
    # Pagination
    stmt = stmt.limit(limit).offset(offset)
    
    # Execute
    result = await db.execute(stmt)
    rows = result.all()
    
    # Build response
    jobs = []
    for job, source_name in rows:
        job_dict = {
            "id": job.id,
            "source_id": job.source_id,
            "source_name": source_name,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "url": job.url,
            "status": job.status,
            "is_new": job.is_new,
            "discovered_at": job.discovered_at,
        }
        jobs.append(JobResponse(**job_dict))
    
    return jobs


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats(db: AsyncSession = Depends(get_db)):
    """Get job statistics for the dashboard.
    
    Returns:
    - total_jobs: Total number of jobs in the database
    - new_jobs_24h: Jobs discovered in the last 24 hours
    - new_jobs_7d: Jobs discovered in the last 7 days
    - by_status: Count of jobs grouped by status
    """
    # Total jobs
    total_stmt = select(func.count(Job.id))
    total_result = await db.execute(total_stmt)
    total_jobs = total_result.scalar() or 0
    
    # New jobs in last 24 hours
    now = datetime.utcnow()
    jobs_24h_stmt = select(func.count(Job.id)).where(
        Job.discovered_at >= now - timedelta(days=1)
    )
    jobs_24h_result = await db.execute(jobs_24h_stmt)
    new_jobs_24h = jobs_24h_result.scalar() or 0
    
    # New jobs in last 7 days
    jobs_7d_stmt = select(func.count(Job.id)).where(
        Job.discovered_at >= now - timedelta(days=7)
    )
    jobs_7d_result = await db.execute(jobs_7d_stmt)
    new_jobs_7d = jobs_7d_result.scalar() or 0
    
    # Jobs by status
    status_stmt = select(Job.status, func.count(Job.id)).group_by(Job.status)
    status_result = await db.execute(status_stmt)
    by_status = {row[0]: row[1] for row in status_result}
    
    return JobStatsResponse(
        total_jobs=total_jobs,
        new_jobs_24h=new_jobs_24h,
        new_jobs_7d=new_jobs_7d,
        by_status=by_status,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single job by ID.
    
    Also marks the job as viewed (is_new = False) if it was new.
    """
    # Fetch job with source name
    stmt = select(Job, JobSource.portal_name).join(
        JobSource, Job.source_id == JobSource.id
    ).where(Job.id == job_id)
    
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job, source_name = row
    
    # Mark as viewed if it was new
    if job.is_new:
        job.is_new = False
        if job.status == "New":
            job.status = "Viewed"
        await db.commit()
    
    # Build response
    job_dict = {
        "id": job.id,
        "source_id": job.source_id,
        "source_name": source_name,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "url": job.url,
        "status": job.status,
        "is_new": job.is_new,
        "discovered_at": job.discovered_at,
    }
    
    return JobResponse(**job_dict)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    update_data: JobUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a job's status or is_new flag."""
    # Fetch job with source name in a single query
    stmt = select(Job, JobSource.portal_name).join(
        JobSource, Job.source_id == JobSource.id
    ).where(Job.id == job_id)
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    job, source_name = row

    # Update fields
    if update_data.status is not None:
        job.status = update_data.status
    if update_data.is_new is not None:
        job.is_new = update_data.is_new

    await db.commit()

    # Build response from in-memory job object (no refresh needed — values were set above)
    job_dict = {
        "id": job.id,
        "source_id": job.source_id,
        "source_name": source_name,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "url": job.url,
        "status": job.status,
        "is_new": job.is_new,
        "discovered_at": job.discovered_at,
    }

    return JobResponse(**job_dict)


@router.post("/bulk-skip")
async def bulk_skip_jobs(
    request: BulkSkipRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bulk skip selected jobs (set status to 'Skipped')."""
    # Update all jobs in the list
    stmt = select(Job).where(Job.id.in_(request.job_ids))
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found with provided IDs")
    
    updated_count = 0
    for job in jobs:
        if job.status != "Skipped":
            job.status = "Skipped"
            job.is_new = False
            updated_count += 1
    
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Skipped {updated_count} job(s)",
        "updated_count": updated_count,
    }


@router.post("/{job_id}/generate-cv")
async def generate_cv(job_id: int, db: AsyncSession = Depends(get_db)):
    """Generate a tailored CV for a specific job.
    
    Steps:
    1. Fetch job details and verify it exists
    2. Fetch the user's CV profile
    3. Use OpenAI to tailor CV for this job
    4. Generate PDF from tailored content
    5. Save PDF and update job record
    """
    # Fetch job
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch CV profile first — if missing, this is the primary error to surface
    cv_stmt = select(CVProfile).limit(1)
    cv_result = await db.execute(cv_stmt)
    cv_profile = cv_result.scalar_one_or_none()

    if not cv_profile:
        raise HTTPException(
            status_code=400,
            detail="No CV profile found. Please upload and configure your CV first."
        )

    # Check if job has a sufficient description
    if not job.description or len(job.description.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short or missing. Cannot generate tailored CV."
        )
    
    # Prepare CV data
    cv_data = {
        "personal_info": cv_profile.personal_info or {},
        "summary": cv_profile.summary or "",
        "work_experience": cv_profile.work_experience or [],
        "education": cv_profile.education or [],
        "skills": cv_profile.skills or [],
        "certifications": cv_profile.certifications or [],
    }
    
    # Validate CV has minimum content
    if not cv_data["personal_info"].get("name"):
        raise HTTPException(
            status_code=400,
            detail="CV profile is incomplete. Please add at least your name."
        )
    
    try:
        # Tailor CV using OpenAI
        tailored_cv = await tailor_cv_for_job(
            cv_data=cv_data,
            job_title=job.title,
            job_company=job.company or "the company",
            job_description=job.description,
        )
        
        # Generate PDF filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"cv_{job.id}_{timestamp}.pdf"
        
        # Ensure output directory exists
        output_dir = Path(settings.cv_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF
        pdf_path = output_dir / filename
        pdf_bytes = generate_cv_pdf(tailored_cv, output_path=str(pdf_path))
        
        # Update job record
        job.tailored_cv = tailored_cv
        job.cv_pdf_path = str(pdf_path)
        job.cv_generated_at = datetime.utcnow()
        job.status = "CV Generated"
        
        await db.commit()
        
        return {
            "status": "success",
            "message": "CV generated successfully",
            "job_id": job.id,
            "cv_path": str(pdf_path),
            "filename": filename,
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CV: {str(e)}"
        )


@router.get("/{job_id}/cv")
async def download_cv(job_id: int, db: AsyncSession = Depends(get_db)):
    """Download the generated CV PDF for a job.
    
    Returns a 404 if:
    - Job doesn't exist
    - CV hasn't been generated for this job
    - PDF file is missing from disk
    """
    # Fetch job
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if CV has been generated
    if not job.cv_pdf_path:
        raise HTTPException(
            status_code=404,
            detail="No CV has been generated for this job yet. Use POST /api/jobs/{id}/generate-cv first."
        )
    
    # Check if file exists
    pdf_path = Path(job.cv_pdf_path)
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="CV PDF file not found on disk. It may have been deleted."
        )
    
    # Prepare filename for download
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in job.title)
    safe_company = "".join(c if c.isalnum() or c in " -_" else "_" for c in job.company) if job.company else "Company"
    download_filename = f"CV_{safe_company}_{safe_title}.pdf"
    
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=download_filename,
    )
