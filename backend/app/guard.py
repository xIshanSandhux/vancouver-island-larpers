"""Abuse and load protection for a public demo URL (architecture.md section 10).

The app is open to the internet during judging while our model credit and Render compute
are finite. These limits are about protecting the demo, not about security.
"""

import json
import time
from collections import deque
from pathlib import Path

from app.config import get_settings
from app.models import CHECK_MAX_CHARS, GENERATE_MAX_CHARS

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Extendable without a code change: data/blocked_terms.json overrides this list.
# The model prompts are the main defence; this only stops the obvious cases cheaply.
_DEFAULT_BLOCKED: list[str] = ["kill yourself", "kys "]


class GuardError(Exception):
    """Rejected before any model or Render call. `code` matches the ApiError contract."""

    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _blocked_terms() -> list[str]:
    path = _DATA_DIR / "blocked_terms.json"
    if path.exists():
        return [t.lower() for t in json.loads(path.read_text())]
    return _DEFAULT_BLOCKED


def check_text(mode: str, text: str) -> str:
    """Length, emptiness, control characters and the blocklist."""
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch >= " ").strip()
    if not cleaned:
        raise GuardError("invalid_input", "Type something first.", 400)
    limit = GENERATE_MAX_CHARS if mode == "generate" else CHECK_MAX_CHARS
    if len(cleaned) > limit:
        raise GuardError("invalid_input", f"Keep it under {limit} characters.", 400)
    lowered = cleaned.lower()
    if any(term in lowered for term in _blocked_terms()):
        raise GuardError("invalid_input", "That input is not something we will write about.", 400)
    return cleaned


class RateLimiter:
    """Per-IP cooldown and hourly caps, plus a global hourly cap on model spend."""

    def __init__(self) -> None:
        self._per_ip: dict[str, deque[float]] = {}
        self._global: deque[float] = deque()

    def check(self, ip: str) -> None:
        settings = get_settings()
        now = time.monotonic()
        hour_ago = now - 3600

        while self._global and self._global[0] < hour_ago:
            self._global.popleft()
        if len(self._global) >= settings.max_runs_per_hour:
            raise GuardError("busy", "This demo has hit its hourly limit. Try again later.", 429)

        history = self._per_ip.setdefault(ip, deque())
        while history and history[0] < hour_ago:
            history.popleft()
        if history and now - history[-1] < settings.per_ip_cooldown_seconds:
            raise GuardError("busy", "One run at a time, please. Try again in a few seconds.", 429)
        if len(history) >= settings.per_ip_runs_per_hour:
            raise GuardError("busy", "You have run this a lot. Try again later.", 429)

        history.append(now)
        self._global.append(now)


limiter = RateLimiter()


def client_ip(forwarded_for: str | None, fallback: str | None) -> str:
    """Render sits behind a proxy, so the real client is first in X-Forwarded-For."""
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return fallback or "unknown"
