from celery import Celery

from app.config import settings

celery_app = Celery(
    "alpcan",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min max per task
    worker_prefetch_multiplier=1,  # One task at a time per worker (GPU bound)
)
