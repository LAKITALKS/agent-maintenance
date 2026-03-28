"""Stub embedding provider — replace with a real backend for production use."""

from __future__ import annotations

import hashlib

from agent_maintenance.providers.base import EmbeddingProvider


class StubEmbeddingProvider(EmbeddingProvider):
    """Deterministic stub that produces pseudo-embeddings from text hashes.

    Useful for testing the pipeline without an external API.
    Do NOT use for real similarity comparisons.
    """

    _DIM = 64

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_embed(t) for t in texts]

    def _hash_embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        # Produce a normalised float vector from the hash bytes
        raw = [b / 255.0 for b in digest]
        # Pad or trim to target dimension
        while len(raw) < self._DIM:
            raw += raw
        return raw[: self._DIM]
