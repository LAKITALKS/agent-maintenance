"""Tests for AnthropicProvider and the LLM factory."""

from __future__ import annotations

import builtins
import warnings
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agent_maintenance.providers.factory import get_llm_provider
from agent_maintenance.providers.llm import StubLLMProvider

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_mock_sdk(response_text: str = "LLM output") -> MagicMock:
    """Return a minimal mock of the anthropic SDK module."""
    sdk = MagicMock()
    sdk.Anthropic.return_value.messages.create.return_value.content = [
        MagicMock(text=response_text)
    ]
    # Make exception classes real subclasses of Exception so they can be caught
    sdk.AuthenticationError = type("AuthenticationError", (Exception,), {})
    sdk.RateLimitError = type("RateLimitError", (Exception,), {})
    sdk.APITimeoutError = type("APITimeoutError", (Exception,), {})
    sdk.APIStatusError = type("APIStatusError", (Exception,), {"status_code": 500})
    sdk.APIError = type("APIError", (Exception,), {})
    return sdk


# ── AnthropicProvider unit tests ───────────────────────────────────────────────

class TestAnthropicProvider:
    def test_raises_import_error_when_sdk_missing(self) -> None:
        real_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "anthropic":
                raise ImportError("mocked missing SDK")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Force re-import of the provider module via direct instantiation attempt
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            with pytest.raises(ImportError, match="pip install"):
                mod.AnthropicProvider(api_key="sk-test")

    def test_raises_value_error_when_key_empty(self) -> None:
        mock_sdk = _make_mock_sdk()
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is empty"):
                mod.AnthropicProvider(api_key="")

    def test_raises_value_error_when_key_whitespace(self) -> None:
        mock_sdk = _make_mock_sdk()
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is empty"):
                mod.AnthropicProvider(api_key="   ")

    def test_complete_returns_text(self) -> None:
        mock_sdk = _make_mock_sdk(response_text="Merged skill content")
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-test-valid")
            result = provider.complete("Merge these skills", system="You are helpful")
            assert result == "Merged skill content"

    def test_complete_passes_system_prompt(self) -> None:
        mock_sdk = _make_mock_sdk()
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-test")
            provider.complete("prompt", system="system instructions")
            call_kwargs = mock_sdk.Anthropic.return_value.messages.create.call_args[1]
            assert call_kwargs["system"] == "system instructions"

    def test_complete_omits_system_when_empty(self) -> None:
        mock_sdk = _make_mock_sdk()
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-test")
            provider.complete("prompt")
            call_kwargs = mock_sdk.Anthropic.return_value.messages.create.call_args[1]
            assert "system" not in call_kwargs

    def test_auth_error_raises_runtime_without_key(self) -> None:
        mock_sdk = _make_mock_sdk()
        mock_sdk.Anthropic.return_value.messages.create.side_effect = (
            mock_sdk.AuthenticationError("bad key")
        )
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-bad")
            with pytest.raises(RuntimeError) as exc_info:
                provider.complete("prompt")
            # Error message must not contain the key
            assert "sk-bad" not in str(exc_info.value)
            assert "authentication" in str(exc_info.value).lower()

    def test_rate_limit_error_raises_runtime(self) -> None:
        mock_sdk = _make_mock_sdk()
        mock_sdk.Anthropic.return_value.messages.create.side_effect = (
            mock_sdk.RateLimitError("rate limited")
        )
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-test")
            with pytest.raises(RuntimeError, match="rate limit"):
                provider.complete("prompt")

    def test_timeout_error_raises_runtime(self) -> None:
        mock_sdk = _make_mock_sdk()
        mock_sdk.Anthropic.return_value.messages.create.side_effect = (
            mock_sdk.APITimeoutError("timed out")
        )
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-test")
            with pytest.raises(RuntimeError, match="timed out"):
                provider.complete("prompt")

    def test_repr_does_not_contain_api_key(self) -> None:
        mock_sdk = _make_mock_sdk()
        with patch.dict("sys.modules", {"anthropic": mock_sdk}):
            import importlib

            import agent_maintenance.providers.anthropic as mod
            importlib.reload(mod)
            provider = mod.AnthropicProvider(api_key="sk-super-secret")
            assert "sk-super-secret" not in repr(provider)


# ── Factory tests ──────────────────────────────────────────────────────────────

class TestGetLLMProviderFactory:
    def test_returns_stub_when_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        provider = get_llm_provider()
        assert isinstance(provider, StubLLMProvider)

    def test_returns_stub_when_key_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        provider = get_llm_provider()
        assert isinstance(provider, StubLLMProvider)

    def test_warns_when_key_set_but_sdk_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        real_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "anthropic":
                raise ImportError("mocked missing SDK")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                provider = get_llm_provider()

        assert isinstance(provider, StubLLMProvider)
        assert any("pip install" in str(w.message).lower() for w in caught)

    def test_warning_does_not_contain_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-very-secret-key")
        real_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "anthropic":
                raise ImportError("mocked")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                get_llm_provider()

        for w in caught:
            assert "sk-very-secret-key" not in str(w.message)

    def test_returns_anthropic_provider_when_key_and_sdk_present(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-valid")

        # The factory imports AnthropicProvider lazily; patch the provider module
        # so the local import inside get_llm_provider() resolves to our fake class.
        class _FakeAnthropicProvider:
            DEFAULT_MODEL = "claude-haiku-4-5-20251001"

            def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
                pass

        fake_mod = MagicMock()
        fake_mod.AnthropicProvider = _FakeAnthropicProvider

        with patch.dict("sys.modules", {"agent_maintenance.providers.anthropic": fake_mod}):
            import importlib

            import agent_maintenance.providers.factory as factory_mod
            importlib.reload(factory_mod)
            provider = factory_mod.get_llm_provider()

        assert isinstance(provider, _FakeAnthropicProvider)
