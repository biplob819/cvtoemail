"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "auto_job_apply",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.job_monitor"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Celery Beat schedule - default 5x per day
# Job monitoring runs at: 8 AM, 11 AM, 2 PM, 5 PM, 8 PM UTC
# CV generation runs 15 minutes after each monitoring cycle
celery_app.conf.beat_schedule = {
    "monitor-jobs-morning": {
        "task": "app.tasks.job_monitor.monitor_all_sources",
        "schedule": crontab(hour=8, minute=0),  # 8 AM UTC
    },
    "generate-cvs-morning": {
        "task": "app.tasks.job_monitor.generate_cvs_for_new_jobs",
        "schedule": crontab(hour=8, minute=15),  # 8:15 AM UTC (15 min after monitoring)
    },
    "monitor-jobs-late-morning": {
        "task": "app.tasks.job_monitor.monitor_all_sources",
        "schedule": crontab(hour=11, minute=0),  # 11 AM UTC
    },
    "generate-cvs-late-morning": {
        "task": "app.tasks.job_monitor.generate_cvs_for_new_jobs",
        "schedule": crontab(hour=11, minute=15),  # 11:15 AM UTC
    },
    "monitor-jobs-afternoon": {
        "task": "app.tasks.job_monitor.monitor_all_sources",
        "schedule": crontab(hour=14, minute=0),  # 2 PM UTC
    },
    "generate-cvs-afternoon": {
        "task": "app.tasks.job_monitor.generate_cvs_for_new_jobs",
        "schedule": crontab(hour=14, minute=15),  # 2:15 PM UTC
    },
    "monitor-jobs-evening": {
        "task": "app.tasks.job_monitor.monitor_all_sources",
        "schedule": crontab(hour=17, minute=0),  # 5 PM UTC
    },
    "generate-cvs-evening": {
        "task": "app.tasks.job_monitor.generate_cvs_for_new_jobs",
        "schedule": crontab(hour=17, minute=15),  # 5:15 PM UTC
    },
    "monitor-jobs-night": {
        "task": "app.tasks.job_monitor.monitor_all_sources",
        "schedule": crontab(hour=20, minute=0),  # 8 PM UTC
    },
    "generate-cvs-night": {
        "task": "app.tasks.job_monitor.generate_cvs_for_new_jobs",
        "schedule": crontab(hour=20, minute=15),  # 8:15 PM UTC
    },
}

if __name__ == "__main__":
    celery_app.start()
