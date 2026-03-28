"""Abstract provider interfaces for pluggable AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Interface for computing text embeddings.

    Implement this to plug in any embedding backend
    (e.g. OpenAI, Cohere, sentence-transformers, Ollama).
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return a list of embedding vectors for the given texts."""
        ...

    def similarity(self, a: list[float], b: list[float]) -> float:
        """Cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class LLMProvider(ABC):
    """Interface for LLM-assisted operations.

    Implement this to plug in any LLM backend
    (e.g. Anthropic Claude, OpenAI, local Ollama model).
    """

    @abstractmethod
    def complete(self, prompt: str, *, system: str = "") -> str:
        """Return a completion for the given prompt."""
        ...
