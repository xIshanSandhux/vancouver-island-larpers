"""The single Workflows app. Task modules import `app` from here and register with @app.task."""

from render import Retry, Workflows

# Every task is retried on exception, timeout or instance error (architecture.md section 6).
RETRY = Retry(max_retries=2, wait_duration_ms=1000, backoff_scaling=1.5)

app = Workflows(default_retry=RETRY, default_timeout=300)
