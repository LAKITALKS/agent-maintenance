"""SentenceTransformer-based embedding provider (local, no API key required)."""

from __future__ import annotations

import os

from agent_maintenance.providers.base import EmbeddingProvider

_INSTALL_HINT = (
    "sentence-transformers is not installed.\n"
    "To enable real semantic similarity, run:\n\n"
    "    pip install agent-maintenance[embeddings]\n"
)


class SentenceTransformerProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers.

    Default model: all-MiniLM-L6-v2
      - ~80 MB, downloads once on first use
      - Fast CPU inference, good semantic quality for skill comparison

    Requires the [embeddings] extra:
        pip install agent-maintenance[embeddings]
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        # Prevent the HuggingFace tokenizers fork/parallelism warning.
        # The warning fires when a tokenizer is first loaded inside a process that
        # was (or may be) forked. setdefault leaves any existing user value untouched.
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]
        except ImportError:
            raise ImportError(_INSTALL_HINT) from None

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]

    def __repr__(self) -> str:
        return f"SentenceTransformerProvider(model={self._model_name!r})"
