"""Model adapter interface — replaceable backend for analysis generation.

Three implementations:
  - FixtureAdapter: deterministic canned responses for demo/testing
  - OpenAIAdapter: calls OpenAI API (implemented in T05)
  - AnthropicAdapter: calls Anthropic API (implemented in T05)

The adapter takes a narrative and returns a raw analysis dict that the
analysis pipeline then validates, applies policy to, and persists.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class AdapterRequest:
    """Input to a model adapter."""

    narrative: str
    report_id: str | None = None
    revision_id: str | None = None
    mode: str = "live"


@dataclass
class AdapterResponse:
    """Raw output from a model adapter, before policy application.

    The `raw` dict follows the extraction schema: hazard findings,
    control findings, evidence spans, and missing facts. The policy
    engine (T05) derives candidate_label and interpretation from this.
    """

    raw: dict
    model_version: str
    prompt_version: str
    duration_ms: int = 0


class ModelAdapter(abc.ABC):
    """Abstract base for all model adapters."""

    @property
    @abc.abstractmethod
    def model_version(self) -> str:
        """Version identifier for this adapter's model."""

    @abc.abstractmethod
    async def analyze(self, request: AdapterRequest) -> AdapterResponse:
        """Analyze a narrative and return structured extraction."""


def get_adapter(provider: str) -> ModelAdapter:
    """Factory: return the configured adapter."""
    if provider == "fixture":
        from app.analysis.fixture_adapter import FixtureAdapter
        return FixtureAdapter()
    elif provider == "openai":
        from app.analysis.openai_adapter import OpenAIAdapter
        return OpenAIAdapter()
    elif provider == "anthropic":
        from app.analysis.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter()
    else:
        raise ValueError(f"Unknown model provider: {provider}")
