from celery import Celery
from app.config import settings
from celery.schedules import crontab

celery_app = Celery(
    "scam_checker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# auto-discover tasks in app/tasks.py
celery_app.autodiscover_tasks(["app"])


celery_app.conf.beat_schedule = {
    "refresh-blocklist-every-6-hours": {
        "task": "app.tasks.refresh_blocklist",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}