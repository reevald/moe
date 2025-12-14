"""
Celery application entrypoint for MOE worker.

This module initializes Celery with all necessary configurations.
"""

import logging

from celery import Celery

from common.config import get_settings
from common.logging_conf import setup_celery_logging

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize logging
setup_celery_logging(
    sentry_dsn=settings.sentry_dsn,
    sentry_environment=settings.sentry_environment,
    sentry_traces_sample_rate=settings.sentry_traces_sample_rate,
    log_level="DEBUG" if settings.debug else "INFO"
)

# Create Celery app
celery_app = Celery(
    "moe_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.tasks.submission_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

logger.info("Celery app initialized successfully")


if __name__ == "__main__":
    celery_app.start()
