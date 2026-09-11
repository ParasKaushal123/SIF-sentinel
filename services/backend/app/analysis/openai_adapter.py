"""OpenAI-backed extraction adapter.

Requires MODEL_API_KEY and the `openai` package. The SDK is imported lazily so
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


class OpenAIAdapter(ModelAdapter):
    @property
    def model_version(self) -> str:
        return f"openai:{settings.model_name}"

    async def analyze(self, request: AdapterRequest) -> AdapterResponse:
        try:
            from openai import AsyncOpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "openai package not installed. `pip install openai` or use MODEL_PROVIDER=fixture."
            ) from e

        if not settings.model_api_key:
            raise RuntimeError("MODEL_API_KEY is not set for the OpenAI provider.")

        client = AsyncOpenAI(api_key=settings.model_api_key)
        start = time.monotonic()

        completion = await client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(request.narrative)},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        content = completion.choices[0].message.content or "{}"
        parsed = safe_json_loads(content)
        raw = coerce_raw(parsed, request.narrative)

        return AdapterResponse(
            raw=raw,
            model_version=self.model_version,
            prompt_version=PROMPT_VERSION,
            duration_ms=duration_ms,
        )
