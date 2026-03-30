"""Tests for the provider factory."""

import warnings
from unittest.mock import patch

from agent_maintenance.providers.embeddings import StubEmbeddingProvider
from agent_maintenance.providers.factory import get_embedding_provider, get_llm_provider
from agent_maintenance.providers.llm import StubLLMProvider
from agent_maintenance.providers.ollama import OllamaProvider


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


class TestGetLLMProvider:
    # reachable is a local import inside get_llm_provider(), so we patch it
    # on the ollama module directly (where it is defined).
    _PATCH = "agent_maintenance.providers.ollama.reachable"

    def test_returns_ollama_when_reachable_and_no_api_key(self, monkeypatch) -> None:
        """When Anthropic key is absent and Ollama is reachable, return OllamaProvider."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with patch(self._PATCH, return_value=True):
            provider = get_llm_provider()

        assert isinstance(provider, OllamaProvider)

    def test_returns_stub_when_ollama_unreachable_and_no_api_key(self, monkeypatch) -> None:
        """When no Anthropic key and Ollama is down, fall back to stub."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with patch(self._PATCH, return_value=False):
            provider = get_llm_provider()

        assert isinstance(provider, StubLLMProvider)

    def test_ollama_host_env_passed_to_reachable(self, monkeypatch) -> None:
        """OLLAMA_HOST env var is forwarded to the reachability check."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_HOST", "http://myserver:9999")

        checked_urls: list[str] = []

        def fake_reachable(url: str, **kwargs) -> bool:
            checked_urls.append(url)
            return False

        with patch(self._PATCH, side_effect=fake_reachable):
            get_llm_provider()

        assert any("myserver:9999" in u for u in checked_urls)

    def test_ollama_model_env_used_when_ollama_active(self, monkeypatch) -> None:
        """OLLAMA_MODEL env var sets the model on the OllamaProvider."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_MODEL", "mistral")

        with patch(self._PATCH, return_value=True):
            provider = get_llm_provider()

        assert isinstance(provider, OllamaProvider)
        assert provider._model == "mistral"

    def test_model_arg_overrides_env(self, monkeypatch) -> None:
        """Explicit model arg takes precedence over OLLAMA_MODEL env var."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")

        with patch(self._PATCH, return_value=True):
            provider = get_llm_provider(model="codellama")

        assert isinstance(provider, OllamaProvider)
        assert provider._model == "codellama"
