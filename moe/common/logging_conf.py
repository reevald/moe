"""
Centralized logging configuration with Sentry.io integration.

This module provides logging setup for both API and Worker services.
"""

import logging
from typing import Optional

import sentry_sdk


def setup_logging(
    sentry_dsn: Optional[str] = None,
    sentry_environment: str = "development",
    sentry_traces_sample_rate: float = 0.1,
    sentry_profiles_sample_rate: float = 1.0,
    log_level: str = "INFO",
    service_name: str = "moe"
) -> None:
    """
    Configure application logging and Sentry integration.

    Args:
        sentry_dsn: Sentry DSN URL (if None, Sentry is disabled)
        sentry_environment: Environment name for Sentry
        sentry_traces_sample_rate: Sampling rate for traces (0.0-1.0)
        sentry_profiles_sample_rate: Sampling rate for profiles (0.0-1.0)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        service_name: Name of the service for logging context
    """
    # Configure Python logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Initialize Sentry if DSN is provided
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=sentry_environment,
            traces_sample_rate=sentry_traces_sample_rate,
            profiles_sample_rate=sentry_profiles_sample_rate,
            attach_stacktrace=True,
            send_default_pii=False,
            _experiments={
                "profiles_sample_rate": 0.1,
            }
        )
        logging.info(
            f"Sentry initialized for {service_name} in "
            f"{sentry_environment} environment"
        )
    else:
        logging.info(
            f"Sentry disabled for {service_name} "
            f"(no DSN provided)"
        )


def setup_fastapi_logging(
    sentry_dsn: Optional[str] = None,
    sentry_environment: str = "development",
    sentry_traces_sample_rate: float = 0.1,
    sentry_profiles_sample_rate: float = 1.0,
    log_level: str = "INFO"
) -> None:
    """
    Configure logging for FastAPI service with Sentry.

    Args:
        sentry_dsn: Sentry DSN URL
        sentry_environment: Environment name
        sentry_traces_sample_rate: Trace sampling rate
        log_level: Logging level
    """
    if sentry_dsn:
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=sentry_environment,
            traces_sample_rate=sentry_traces_sample_rate,
            profiles_sample_rate=sentry_profiles_sample_rate,
            integrations=[
                StarletteIntegration(
                    transaction_style="endpoint"
                ),
                FastApiIntegration(
                    transaction_style="endpoint"
                ),
            ],
            attach_stacktrace=True,
            send_default_pii=False,
        )

    setup_logging(
        sentry_dsn=None,
        log_level=log_level,
        service_name="moe-api"
    )


def setup_celery_logging(
    sentry_dsn: Optional[str] = None,
    sentry_environment: str = "development",
    sentry_traces_sample_rate: float = 0.1,
    sentry_profiles_sample_rate: float = 1.0,
    log_level: str = "INFO"
) -> None:
    """
    Configure logging for Celery worker with Sentry.

    Args:
        sentry_dsn: Sentry DSN URL
        sentry_environment: Environment name
        sentry_traces_sample_rate: Trace sampling rate
        sentry_profiles_sample_rate: Profile sampling rate
        log_level: Logging level
    """
    if sentry_dsn:
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=sentry_environment,
            traces_sample_rate=sentry_traces_sample_rate,
            profiles_sample_rate=sentry_profiles_sample_rate,
            integrations=[
                CeleryIntegration(
                    monitor_beat_tasks=True,
                    propagate_traces=True,
                ),
            ],
            attach_stacktrace=True,
            send_default_pii=False,
        )

    setup_logging(
        sentry_dsn=None,
        log_level=log_level,
        service_name="moe-worker"
    )
