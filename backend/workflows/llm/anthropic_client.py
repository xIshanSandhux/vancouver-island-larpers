"""The only model client in the project (architecture.md section 12).

Notes that cost real debugging time if forgotten:
  * This API version has no `temperature`. Sending one is a 400.
  * Haiku 5.5 runs thinking by default and bills it as output. We disable it, which the
    model accepts at effort "high" or below.
  * Structured outputs make the reply schema-valid JSON. We still parse defensively so
    the pipeline survives the flag being turned off.
  * User text is data, never instructions: callers wrap it in delimiters and it never
    goes in the system prompt.
"""

import asyncio
import json
import logging
import re
from typing import Any

from anthropic import APIStatusError, AsyncAnthropic

from app.config import get_settings

log = logging.getLogger("workflows.llm")


class LLMError(Exception):
    """A model call that could not produce usable JSON."""


class LLMRefusal(LLMError):
    """The model declined the request. Callers fall back to a safe default."""


_client: AsyncAnthropic | None = None
_semaphore: asyncio.Semaphore | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncAnthropic(
            api_key=settings.anthropic_api_key or None,
            timeout=settings.llm_timeout_seconds,
            max_retries=1,
        )
    return _client


def get_semaphore() -> asyncio.Semaphore:
    """Caps concurrent outgoing model calls inside one task run."""
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(get_settings().llm_concurrency)
    return _semaphore


_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def extract_json(text: str) -> Any:
    """Parse JSON from a model reply, tolerating code fences and surrounding prose."""
    cleaned = _FENCE.sub("", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost {...} or [...] span.
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = cleaned.find(opener), cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError(f"no JSON in model reply: {cleaned[:200]!r}")


def _response_text(message: Any) -> str:
    return "".join(b.text for b in message.content if getattr(b, "type", None) == "text")


async def call_json(
    *,
    system: str,
    user: str,
    schema: dict[str, Any] | None = None,
    max_tokens: int = 1024,
    model: str | None = None,
) -> Any:
    """One model call that must return JSON. Retries once with a reminder on bad JSON."""
    settings = get_settings()
    client = get_client()

    kwargs: dict[str, Any] = {
        "model": model or settings.claude_model,
        "max_tokens": max_tokens,
        "system": system,
    }
    output_config: dict[str, Any] = {"effort": settings.llm_effort}
    if schema and settings.llm_structured_outputs:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    kwargs["output_config"] = output_config
    if settings.llm_thinking_disabled:
        kwargs["thinking"] = {"type": "disabled"}

    messages = [{"role": "user", "content": user}]
    last_error: Exception | None = None

    for attempt in (1, 2):
        try:
            async with get_semaphore():
                message = await client.messages.create(messages=messages, **kwargs)
        except APIStatusError as exc:
            # 4xx is a bug in our request; retrying it wastes the budget.
            if exc.status_code < 500:
                raise LLMError(f"model rejected the request: {exc.status_code}") from exc
            last_error = exc
            await asyncio.sleep(0.5 * attempt)
            continue

        if getattr(message, "stop_reason", None) == "refusal":
            raise LLMRefusal("model declined this input")

        text = _response_text(message)
        try:
            return extract_json(text)
        except LLMError as exc:
            last_error = exc
            log.warning("bad JSON from model (attempt %s)", attempt)
            messages = [
                {"role": "user", "content": user},
                {"role": "assistant", "content": text[:500] or "(empty)"},
                {"role": "user", "content": "That was not valid JSON. Reply with only the JSON object, nothing else."},
            ]

    raise LLMError(f"model never returned usable JSON: {last_error}")
