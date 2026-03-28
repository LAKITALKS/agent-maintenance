"""Stub LLM provider — replace with a real backend for production use."""

from __future__ import annotations

from agent_maintenance.providers.base import LLMProvider


class StubLLMProvider(LLMProvider):
    """Stub that returns a fixed placeholder response.

    Useful for wiring up the pipeline without an external API.
    Replace with an Anthropic, OpenAI, or Ollama provider for real use.
    """

    def complete(self, prompt: str, *, system: str = "") -> str:
        return (
            "[StubLLMProvider] This is a placeholder response. "
            "Configure a real LLM provider to enable AI-assisted operations."
        )
