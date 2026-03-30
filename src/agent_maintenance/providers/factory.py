"""Factory for resolving the active embedding and LLM providers."""

from __future__ import annotations

import os
import warnings

from agent_maintenance.providers.base import EmbeddingProvider, LLMProvider


def get_embedding_provider(model_name: str | None = None) -> EmbeddingProvider:
    """Return the best available embedding provider.

    Resolution order:
    1. SentenceTransformerProvider — if sentence-transformers is installed.
    2. StubEmbeddingProvider       — fallback, with a console warning.

    Args:
        model_name: Override the default ST model name. Ignored when falling back to stub.
    """
    try:
        from agent_maintenance.providers.sentence_transformers import (
            SentenceTransformerProvider,
        )

        name = model_name or SentenceTransformerProvider.DEFAULT_MODEL
        return SentenceTransformerProvider(name)

    except ImportError:
        warnings.warn(
            "sentence-transformers is not installed — falling back to stub embeddings.\n"
            "Similarity scores will not be semantically meaningful.\n"
            "To fix: pip install agent-maintenance[embeddings]",
            UserWarning,
            stacklevel=2,
        )
        from agent_maintenance.providers.embeddings import StubEmbeddingProvider

        return StubEmbeddingProvider()


def get_llm_provider(model: str | None = None) -> LLMProvider:
    """Return the best available LLM provider.

    Resolution order:
    1. AnthropicProvider — when ANTHROPIC_API_KEY is set and the SDK is installed.
    2. OllamaProvider    — when Ollama is reachable at OLLAMA_HOST (default: localhost:11434).
    3. StubLLMProvider   — fallback; the merger signals structural mode in its output.

    Environment variables
    ---------------------
    ANTHROPIC_API_KEY  Anthropic secret key.
    OLLAMA_HOST        Ollama server URL (default: http://localhost:11434).
    OLLAMA_MODEL       Ollama model override (default: llama3.2).

    Args:
        model: Override the provider's default model name.
               Applied to whichever provider is selected.
    """
    # ── 1. Anthropic ──────────────────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        try:
            from agent_maintenance.providers.anthropic import AnthropicProvider

            chosen_model = model or AnthropicProvider.DEFAULT_MODEL
            return AnthropicProvider(api_key=api_key, model=chosen_model)

        except ImportError:
            warnings.warn(
                "ANTHROPIC_API_KEY is set but the anthropic SDK is not installed.\n"
                "Falling back to next available provider.\n"
                "To enable: pip install agent-maintenance[llm]",
                UserWarning,
                stacklevel=2,
            )

    # ── 2. Ollama (local-first, no extra dependencies) ────────────────────
    from agent_maintenance.providers.ollama import OllamaProvider, reachable

    ollama_host = os.environ.get("OLLAMA_HOST", OllamaProvider.DEFAULT_HOST)
    ollama_model = model or os.environ.get("OLLAMA_MODEL", OllamaProvider.DEFAULT_MODEL)

    if reachable(ollama_host):
        return OllamaProvider(base_url=ollama_host, model=ollama_model)

    # ── 3. Stub fallback ─────────────────────────────────────────────────
    from agent_maintenance.providers.llm import StubLLMProvider

    return StubLLMProvider()
