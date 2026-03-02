"""Celery task for monitoring job sources and detecting new jobs."""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import httpx

from app.tasks.celery_app import celery_app
from app.models.job_source import JobSource
from app.models.job import Job
from app.models.cv import CVProfile
from app.models.settings import AppSettings
from app.models.application import Application
from app.services.scraper import scrape_source, hash_job_url
from app.services.cv_writer import tailor_cv_for_job
from app.services.pdf_generator import generate_cv_pdf
from app.services.email_sender import create_email_sender, EmailSendError
from app.utils.crypto import decrypt_string
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Create a sync engine for Celery tasks
# Celery tasks run in separate worker processes, so we need a sync connection
sync_engine = create_engine(settings.database_url_sync, echo=settings.debug)
SyncSession = sessionmaker(bind=sync_engine, expire_on_commit=False)


async def fetch_job_description(job_url: str) -> str:
    """Fetch the full job description from a job detail page.
    
    Args:
        job_url: The URL of the job detail page
        
    Returns:
        The extracted job description text, or empty string if failed
    """
    try:
        # Use a simple httpx fetch with timeout
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(20.0),
        ) as client:
            response = await client.get(job_url)
            response.raise_for_status()
            
            # Parse the HTML and extract text content
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Look for common description container patterns
            description_selectors = [
                "[class*='description']",
                "[class*='job-detail']",
                "[class*='job-content']",
                "[id*='description']",
                "[id*='job-detail']",
                ".content",
                "article",
                "main",
            ]
            
            description_text = ""
            for selector in description_selectors:
                elements = soup.select(selector)
                if elements:
                    # Get text from the first matching element
                    description_text = elements[0].get_text(separator="\n", strip=True)
                    if len(description_text) > 100:  # Only use if meaningful content
                        break
            
            # Fallback: get all text from body if no specific container found
            if not description_text:
                body = soup.find("body")
                if body:
                    description_text = body.get_text(separator="\n", strip=True)
            
            # Clean up and limit length
            lines = [line.strip() for line in description_text.split("\n") if line.strip()]
            description_text = "\n".join(lines)
            
            # Limit to ~10000 characters to avoid huge descriptions
            if len(description_text) > 10000:
                description_text = description_text[:10000] + "..."
            
            return description_text
            
    except Exception as e:
        logger.warning(f"Failed to fetch description from {job_url}: {str(e)}")
        return ""


async def process_source(source_id: int, source_url: str, source_name: str) -> dict:
    """Process a single job source: scrape, deduplicate, and store new jobs.
    
    Args:
        source_id: Database ID of the job source
        source_url: URL to scrape
        source_name: Portal name for logging
        
    Returns:
        dict with results: jobs_found, new_jobs, errors
    """
    result = {
        "source_id": source_id,
        "source_name": source_name,
        "jobs_found": 0,
        "new_jobs": 0,
        "errors": [],
    }
    
    try:
        # Scrape the source
        logger.info(f"Scraping source: {source_name} ({source_url})")
        job_listings = await scrape_source(source_url)
        result["jobs_found"] = len(job_listings)

        if not job_listings:
            logger.info(f"No jobs found for {source_name}")

        # Always open a DB session to process results and update last_checked
        with SyncSession() as session:
            if job_listings:
                # Get existing job URLs for this source (for deduplication)
                stmt = select(Job.url).where(Job.source_id == source_id)
                existing_urls = set(session.execute(stmt).scalars().all())

                # Process each job listing
                for job_data in job_listings:
                    job_url = job_data.get("url")
                    if not job_url:
                        continue

                    # Deduplicate by URL
                    if job_url in existing_urls:
                        continue

                    try:
                        # Fetch full job description
                        logger.info(f"Fetching description for: {job_data.get('title', 'Untitled')}")
                        description = await fetch_job_description(job_url)

                        # Create new job record
                        new_job = Job(
                            source_id=source_id,
                            title=job_data.get("title", "Untitled Position")[:200],
                            company=job_data.get("company", "")[:200],
                            location=job_data.get("location", "")[:200],
                            description=description,
                            url=job_url,
                            status="New",
                            is_new=True,
                        )

                        session.add(new_job)
                        session.commit()

                        result["new_jobs"] += 1
                        logger.info(f"Stored new job: {new_job.title} at {new_job.company}")

                    except Exception as e:
                        error_msg = f"Failed to store job {job_url}: {str(e)}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
                        # Continue processing other jobs
                        continue

            # Always update last_checked timestamp for the source
            stmt = select(JobSource).where(JobSource.id == source_id)
            source = session.execute(stmt).scalar_one_or_none()
            if source:
                source.last_checked = datetime.utcnow()
                session.commit()
        
    except Exception as e:
        error_msg = f"Failed to process source {source_name}: {str(e)}"
        logger.error(error_msg)
        result["errors"].append(error_msg)
    
    return result


@celery_app.task(
    name="app.tasks.job_monitor.monitor_all_sources",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def monitor_all_sources(self):
    """Celery task: Monitor all active job sources and detect new jobs.
    
    This task:
    1. Fetches all active job sources
    2. Scrapes each source for job listings
    3. Deduplicates against existing jobs (by URL)
    4. Stores new jobs with status "New" and is_new=True
    5. Fetches full job descriptions for new jobs
    6. Updates last_checked timestamp for each source
    7. Logs results and errors
    
    Runs on a schedule defined in celery_app.py (default: 5x/day)
    """
    logger.info("=" * 80)
    logger.info("Starting job monitoring task")
    logger.info("=" * 80)
    
    start_time = datetime.utcnow()
    total_jobs_found = 0
    total_new_jobs = 0
    all_errors = []
    
    try:
        # Get all active sources
        with SyncSession() as session:
            stmt = select(JobSource).where(JobSource.is_active == True)
            active_sources = session.execute(stmt).scalars().all()
            
            if not active_sources:
                logger.info("No active sources to monitor")
                return {
                    "status": "completed",
                    "sources_processed": 0,
                    "total_jobs_found": 0,
                    "total_new_jobs": 0,
                    "errors": [],
                }
        
        logger.info(f"Found {len(active_sources)} active source(s) to monitor")
        
        # Process each source
        results = []
        for source in active_sources:
            try:
                # Run the async scraping in an event loop
                result = asyncio.run(process_source(
                    source_id=source.id,
                    source_url=source.url,
                    source_name=source.portal_name,
                ))
                results.append(result)
                
                total_jobs_found += result["jobs_found"]
                total_new_jobs += result["new_jobs"]
                all_errors.extend(result["errors"])
                
            except Exception as e:
                error_msg = f"Fatal error processing source {source.portal_name}: {str(e)}"
                logger.error(error_msg)
                all_errors.append(error_msg)
                # Continue with other sources - don't let one failure block others
                continue
        
        # Log summary
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info("=" * 80)
        logger.info(f"Job monitoring completed in {duration:.2f} seconds")
        logger.info(f"Sources processed: {len(active_sources)}")
        logger.info(f"Total jobs found: {total_jobs_found}")
        logger.info(f"New jobs stored: {total_new_jobs}")
        logger.info(f"Errors: {len(all_errors)}")
        logger.info("=" * 80)
        
        return {
            "status": "completed",
            "sources_processed": len(active_sources),
            "total_jobs_found": total_jobs_found,
            "total_new_jobs": total_new_jobs,
            "errors": all_errors,
            "duration_seconds": duration,
        }
        
    except Exception as e:
        logger.error(f"Fatal error in monitor_all_sources: {str(e)}")
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.job_monitor.generate_cvs_for_new_jobs",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def generate_cvs_for_new_jobs(self):
    """Celery task: Generate tailored CVs for all new jobs.
    
    This task:
    1. Fetches all jobs with status "New" that don't have a CV yet
    2. Fetches the user's CV profile
    3. For each job, generates a tailored CV using OpenAI
    4. Generates PDF and saves to disk
    5. Updates job status to "CV Generated"
    6. Logs results and errors
    
    Can be run manually or on a schedule after job monitoring.
    """
    logger.info("=" * 80)
    logger.info("Starting CV generation task for new jobs")
    logger.info("=" * 80)
    
    start_time = datetime.utcnow()
    total_jobs_processed = 0
    successful_cvs = 0
    failed_cvs = 0
    errors = []
    
    try:
        with SyncSession() as session:
            # Get CV profile
            cv_stmt = select(CVProfile).limit(1)
            cv_profile = session.execute(cv_stmt).scalar_one_or_none()
            
            if not cv_profile:
                logger.warning("No CV profile found. Skipping CV generation.")
                return {
                    "status": "skipped",
                    "reason": "No CV profile found",
                    "jobs_processed": 0,
                }
            
            # Validate CV has minimum content
            if not cv_profile.personal_info or not cv_profile.personal_info.get("name"):
                logger.warning("CV profile is incomplete. Skipping CV generation.")
                return {
                    "status": "skipped",
                    "reason": "CV profile incomplete (missing name)",
                    "jobs_processed": 0,
                }
            
            # Prepare CV data
            cv_data = {
                "personal_info": cv_profile.personal_info or {},
                "summary": cv_profile.summary or "",
                "work_experience": cv_profile.work_experience or [],
                "education": cv_profile.education or [],
                "skills": cv_profile.skills or [],
                "certifications": cv_profile.certifications or [],
            }
            
            # Get all new jobs without CVs that have descriptions
            jobs_stmt = select(Job).where(
                Job.status == "New",
                Job.cv_pdf_path.is_(None),
                Job.description.isnot(None),
            )
            new_jobs = session.execute(jobs_stmt).scalars().all()
            
            if not new_jobs:
                logger.info("No new jobs found that need CV generation")
                return {
                    "status": "completed",
                    "jobs_processed": 0,
                    "successful": 0,
                    "failed": 0,
                }
            
            logger.info(f"Found {len(new_jobs)} job(s) that need CVs")
            
            # Process each job
            for job in new_jobs:
                total_jobs_processed += 1
                
                try:
                    # Skip jobs with very short descriptions
                    if not job.description or len(job.description.strip()) < 50:
                        logger.warning(f"Skipping job {job.id} - description too short")
                        continue
                    
                    logger.info(f"Generating CV for job {job.id}: {job.title} at {job.company}")
                    
                    # Run async CV tailoring
                    tailored_cv = asyncio.run(tailor_cv_for_job(
                        cv_data=cv_data,
                        job_title=job.title,
                        job_company=job.company or "the company",
                        job_description=job.description,
                    ))
                    
                    # Generate PDF
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    filename = f"cv_{job.id}_{timestamp}.pdf"
                    
                    # Ensure output directory exists
                    output_dir = Path(settings.cv_output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    pdf_path = output_dir / filename
                    pdf_bytes = generate_cv_pdf(tailored_cv, output_path=str(pdf_path))
                    
                    # Update job record
                    job.tailored_cv = tailored_cv
                    job.cv_pdf_path = str(pdf_path)
                    job.cv_generated_at = datetime.utcnow()
                    job.status = "CV Generated"
                    session.commit()
                    
                    successful_cvs += 1
                    logger.info(f"Successfully generated CV for job {job.id}")
                    
                    # Trigger email sending task asynchronously
                    send_job_email.delay(job.id)
                    
                except Exception as e:
                    error_msg = f"Failed to generate CV for job {job.id} ({job.title}): {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    failed_cvs += 1
                    # Continue with other jobs
                    continue
        
        # Log summary
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info("=" * 80)
        logger.info(f"CV generation completed in {duration:.2f} seconds")
        logger.info(f"Jobs processed: {total_jobs_processed}")
        logger.info(f"Successful: {successful_cvs}")
        logger.info(f"Failed: {failed_cvs}")
        logger.info("=" * 80)
        
        return {
            "status": "completed",
            "jobs_processed": total_jobs_processed,
            "successful": successful_cvs,
            "failed": failed_cvs,
            "errors": errors,
            "duration_seconds": duration,
        }
        
    except Exception as e:
        logger.error(f"Fatal error in generate_cvs_for_new_jobs: {str(e)}")
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(
    name="app.tasks.job_monitor.send_job_email",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def send_job_email(self, job_id: int):
    """Celery task: Send email notification for a job with tailored CV.
    
    This task:
    1. Fetches the job details and CV PDF path
    2. Gets email settings from AppSettings
    3. Sends email with job details and CV attachment
    4. Logs the application (sent/failed) in Application table
    5. Updates job status to "CV Sent" on success
    
    Args:
        job_id: The ID of the job to send email for
    """
    logger.info(f"Starting email send task for job {job_id}")
    
    try:
        with SyncSession() as session:
            # Get job
            job_stmt = select(Job).where(Job.id == job_id)
            job = session.execute(job_stmt).scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return {"status": "failed", "reason": "Job not found"}
            
            # Get settings
            settings_stmt = select(AppSettings).where(AppSettings.id == 1)
            app_settings = session.execute(settings_stmt).scalar_one_or_none()
            
            if not app_settings:
                logger.warning("No settings found. Email not configured.")
                return {"status": "skipped", "reason": "Settings not configured"}
            
            # Check if email is configured
            if not all([
                app_settings.notification_email,
                app_settings.smtp_host,
                app_settings.smtp_port,
                app_settings.smtp_user,
                app_settings.smtp_password,
            ]):
                logger.warning("Email settings incomplete. Skipping email.")
                return {"status": "skipped", "reason": "Email settings incomplete"}
            
            # Decrypt SMTP password
            smtp_password = decrypt_string(app_settings.smtp_password)
            if not smtp_password:
                logger.error("Failed to decrypt SMTP password")
                return {"status": "failed", "reason": "Failed to decrypt SMTP password"}
            
            # Check if CV PDF exists
            if not job.cv_pdf_path or not Path(job.cv_pdf_path).exists():
                logger.warning(f"CV PDF not found for job {job_id}: {job.cv_pdf_path}")
                cv_pdf_path = None
            else:
                cv_pdf_path = Path(job.cv_pdf_path)
            
            # Create email sender
            email_sender = create_email_sender(
                smtp_host=app_settings.smtp_host,
                smtp_port=app_settings.smtp_port,
                smtp_user=app_settings.smtp_user,
                smtp_password=smtp_password,
                from_email=app_settings.smtp_user,
            )
            
            # Send email
            try:
                email_sender.send_job_notification(
                    to_email=app_settings.notification_email,
                    job_title=job.title,
                    company=job.company or "Unknown Company",
                    location=job.location,
                    job_url=job.url,
                    job_description=job.description[:500] if job.description else None,
                    cv_pdf_path=cv_pdf_path,
                )
                
                # Log successful application
                application = Application(
                    job_id=job.id,
                    cv_path=str(cv_pdf_path) if cv_pdf_path else None,
                    email_sent_to=app_settings.notification_email,
                    status="sent",
                    sent_at=datetime.utcnow(),
                )
                session.add(application)
                
                # Update job status
                job.status = "CV Sent"
                session.commit()
                
                logger.info(f"Email sent successfully for job {job_id}")
                return {
                    "status": "success",
                    "job_id": job_id,
                    "email_sent_to": app_settings.notification_email,
                }
                
            except EmailSendError as e:
                # Log failed application
                application = Application(
                    job_id=job.id,
                    cv_path=str(cv_pdf_path) if cv_pdf_path else None,
                    email_sent_to=app_settings.notification_email,
                    status="failed",
                    error_message=str(e),
                    sent_at=datetime.utcnow(),
                )
                session.add(application)
                session.commit()
                
                logger.error(f"Failed to send email for job {job_id}: {e}")
                # Retry the task
                raise self.retry(exc=e)
    
    except Exception as e:
        logger.error(f"Fatal error in send_job_email for job {job_id}: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(name="app.tasks.job_monitor.test_task")
def test_task():
    """Simple test task to verify Celery is working."""
    logger.info("Test task executed successfully!")
    return {"status": "success", "message": "Celery is working!"}
