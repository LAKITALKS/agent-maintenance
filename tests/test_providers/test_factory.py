"""Tests for the provider factory."""

import warnings

from agent_maintenance.providers.embeddings import StubEmbeddingProvider
from agent_maintenance.providers.factory import get_embedding_provider


class TestGetEmbeddingProvider:
    def test_returns_stub_when_sentence_transformers_missing(self, monkeypatch) -> None:
        """When sentence-transformers is not importable, fall back to stub."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                raise ImportError("mocked missing package")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            provider = get_embedding_provider()

        assert isinstance(provider, StubEmbeddingProvider)
        assert any("stub embeddings" in str(w.message).lower() for w in caught)

    def test_stub_provider_embeds(self) -> None:
        provider = StubEmbeddingProvider()
        vecs = provider.embed(["hello world", "foo bar"])
        assert len(vecs) == 2
        assert all(len(v) == 64 for v in vecs)

    def test_stub_similarity_bounded(self) -> None:
        provider = StubEmbeddingProvider()
        a, b = provider.embed(["text a", "text b"])
        score = provider.similarity(a, b)
        assert 0.0 <= score <= 1.0
