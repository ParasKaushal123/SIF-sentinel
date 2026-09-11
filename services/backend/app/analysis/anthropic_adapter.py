"""Anthropic-backed extraction adapter.

Requires MODEL_API_KEY and the `anthropic` package. The SDK is imported lazily so
the app runs fine without it when MODEL_PROVIDER=fixture (the default).
"""

from __future__ import annotations

import time

from app.analysis.adapter import AdapterRequest, AdapterResponse, ModelAdapter
from app.analysis.extraction_prompt import (
    SYSTEM_PROMPT,
    build_user_prompt,
    coerce_raw,
    safe_json_loads,
)
from app.config import settings

PROMPT_VERSION = "extract-json-v1"


class AnthropicAdapter(ModelAdapter):
    @property
    def model_version(self) -> str:
        return f"anthropic:{settings.model_name}"

    async def analyze(self, request: AdapterRequest) -> AdapterResponse:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "anthropic package not installed. `pip install anthropic` or use MODEL_PROVIDER=fixture."
            ) from e

        if not settings.model_api_key:
            raise RuntimeError("MODEL_API_KEY is not set for the Anthropic provider.")

        client = AsyncAnthropic(api_key=settings.model_api_key)
        start = time.monotonic()

        message = await client.messages.create(
            model=settings.model_name,
            max_tokens=2000,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_user_prompt(request.narrative)},
            ],
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        # Concatenate text blocks
        content = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        ) or "{}"
        parsed = safe_json_loads(content)
        raw = coerce_raw(parsed, request.narrative)

        return AdapterResponse(
            raw=raw,
            model_version=self.model_version,
            prompt_version=PROMPT_VERSION,
            duration_ms=duration_ms,
        )
