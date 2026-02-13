"""Dashboard API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List

from app.database import get_db
from app.models.job_source import JobSource
from app.models.job import Job
from app.models.application import Application

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    active_sources: int
    new_jobs_24h: int
    cvs_sent_7d: int
    last_scan: Optional[str] = None
    total_jobs: int
    total_applications: int


class RecentJob(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    status: str
    discovered_at: datetime
    source_name: str

    class Config:
        from_attributes = True


class SystemStatus(BaseModel):
    celery_running: bool = True  # Placeholder - in production, check Celery health
    next_scan: Optional[str] = None


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    try:
        # Active sources count
        active_sources_result = await db.execute(
            select(func.count()).select_from(JobSource).where(JobSource.is_active == True)
        )
        active_sources = active_sources_result.scalar() or 0
    except Exception:
        active_sources = 0

    try:
        # New jobs in last 24 hours
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        new_jobs_result = await db.execute(
            select(func.count()).select_from(Job).where(
                Job.discovered_at >= cutoff_24h,
                Job.status == "New"
            )
        )
        new_jobs_24h = new_jobs_result.scalar() or 0
    except Exception:
        new_jobs_24h = 0

    try:
        # CVs sent in last 7 days
        cutoff_7d = datetime.utcnow() - timedelta(days=7)
        cvs_sent_result = await db.execute(
            select(func.count()).select_from(Application).where(
                Application.sent_at >= cutoff_7d,
                Application.status == "sent"
            )
        )
        cvs_sent_7d = cvs_sent_result.scalar() or 0
    except Exception:
        cvs_sent_7d = 0

    try:
        # Last scan time
        last_scan_result = await db.execute(
            select(JobSource.last_checked).where(
                JobSource.last_checked.isnot(None)
            ).order_by(JobSource.last_checked.desc()).limit(1)
        )
        last_scan = last_scan_result.scalar()
        last_scan_str = last_scan.isoformat() if last_scan else None
    except Exception:
        last_scan_str = None

    try:
        # Total jobs
        total_jobs_result = await db.execute(select(func.count()).select_from(Job))
        total_jobs = total_jobs_result.scalar() or 0
    except Exception:
        total_jobs = 0

    try:
        # Total applications
        total_apps_result = await db.execute(select(func.count()).select_from(Application))
        total_applications = total_apps_result.scalar() or 0
    except Exception:
        total_applications = 0

    return DashboardStats(
        active_sources=active_sources,
        new_jobs_24h=new_jobs_24h,
        cvs_sent_7d=cvs_sent_7d,
        last_scan=last_scan_str,
        total_jobs=total_jobs,
        total_applications=total_applications,
    )


@router.get("/recent-jobs", response_model=List[RecentJob])
async def get_recent_jobs(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get recent jobs (last 10 by default)."""
    try:
        # Join with job sources to get source name
        stmt = (
            select(Job, JobSource.portal_name)
            .join(JobSource, Job.source_id == JobSource.id)
            .order_by(Job.discovered_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        recent_jobs = []
        for job, source_name in rows:
            recent_jobs.append(RecentJob(
                id=job.id,
                title=job.title,
                company=job.company or "Unknown",
                location=job.location,
                status=job.status,
                discovered_at=job.discovered_at,
                source_name=source_name,
            ))
        
        return recent_jobs
    except Exception:
        return []


@router.get("/system-status", response_model=SystemStatus)
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """Get system status."""
    # In a production system, you would check Celery health here
    # For now, we'll return a simple status
    return SystemStatus(
        celery_running=True,
        next_scan=None,  # Could calculate based on scan frequency
    )
