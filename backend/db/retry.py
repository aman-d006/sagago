from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
import sqlite3
import requests

logger = logging.getLogger(__name__)


RETRYABLE_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    BrokenPipeError,
    ConnectionError,
    TimeoutError,
)

SQLITE_BUSY = "SQLITE_BUSY"
SQLITE_LOCKED = "SQLITE_LOCKED"

def is_retryable_error(exception):
    """Check if error is retryable"""
    if isinstance(exception, RETRYABLE_EXCEPTIONS):
        return True
    if hasattr(exception, 'args') and exception.args:
        if SQLITE_BUSY in str(exception) or SQLITE_LOCKED in str(exception):
            return True
    return False


def with_retry(max_attempts: int = 3, min_wait: float = 1, max_wait: float = 10):
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying database operation (attempt {retry_state.attempt_number}/{max_attempts})"
        ),
        reraise=True
    )

