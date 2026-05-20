"""Retries, circuit breakers, and fallback logic."""

from functools import wraps
from typing import Callable, TypeVar

from circuitbreaker import circuit
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


def with_retry(max_attempts: int | None = None):
    settings = get_settings()
    attempts = max_attempts or settings.agent_max_retries

    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True,
    )


def with_circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    return circuit(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=Exception,
    )


def fallback(default_factory: Callable[[], T]):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning("fallback_triggered", function=func.__name__, error=str(e))
                return default_factory()

        return wrapper

    return decorator
