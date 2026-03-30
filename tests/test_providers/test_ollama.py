"""Tests for the OllamaProvider."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agent_maintenance.providers.ollama import OllamaProvider, reachable


class TestReachable:
    def test_returns_true_when_port_open(self) -> None:
        with patch("socket.create_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=None)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            assert reachable("http://localhost:11434") is True

    def test_returns_false_on_connection_refused(self) -> None:
        with patch("socket.create_connection", side_effect=OSError("refused")):
            assert reachable("http://localhost:11434") is False

    def test_parses_custom_host_and_port(self) -> None:
        captured: list = []

        def fake_connect(addr, timeout):
            captured.append(addr)
            raise OSError("not running")

        with patch("socket.create_connection", side_effect=fake_connect):
            reachable("http://myhost:9999")

        assert captured[0] == ("myhost", 9999)

    def test_defaults_to_localhost_11434(self) -> None:
        captured: list = []

        def fake_connect(addr, timeout):
            captured.append(addr)
            raise OSError("not running")

        with patch("socket.create_connection", side_effect=fake_connect):
            reachable("http://localhost")

        assert captured[0][1] == 11434


class TestOllamaProviderDefaults:
    def test_default_host(self) -> None:
        assert OllamaProvider.DEFAULT_HOST == "http://localhost:11434"

    def test_default_model(self) -> None:
        assert OllamaProvider.DEFAULT_MODEL == "llama3.2"

    def test_init_stores_values(self) -> None:
        provider = OllamaProvider(base_url="http://myhost:9999", model="mistral")
        assert provider._base_url == "http://myhost:9999"
        assert provider._model == "mistral"

    def test_trailing_slash_stripped(self) -> None:
        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert not provider._base_url.endswith("/")


class TestOllamaProviderComplete:
    def _make_response(self, text: str) -> MagicMock:
        """Build a fake urllib response context manager."""
        body = json.dumps({"response": text}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_returns_response_text(self) -> None:
        provider = OllamaProvider()
        mock_resp = self._make_response("Hello from Ollama")

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = provider.complete("Say hello")

        assert result == "Hello from Ollama"

    def test_sends_prompt_in_payload(self) -> None:
        provider = OllamaProvider(model="llama3.2")
        mock_resp = self._make_response("ok")
        captured_req: list = []

        def fake_urlopen(req, timeout):
            captured_req.append(req)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            provider.complete("my prompt")

        payload = json.loads(captured_req[0].data.decode())
        assert payload["prompt"] == "my prompt"
        assert payload["model"] == "llama3.2"
        assert payload["stream"] is False

    def test_sends_system_when_provided(self) -> None:
        provider = OllamaProvider()
        mock_resp = self._make_response("ok")
        captured_req: list = []

        def fake_urlopen(req, timeout):
            captured_req.append(req)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            provider.complete("prompt", system="you are helpful")

        payload = json.loads(captured_req[0].data.decode())
        assert payload["system"] == "you are helpful"

    def test_omits_system_when_empty(self) -> None:
        provider = OllamaProvider()
        mock_resp = self._make_response("ok")
        captured_req: list = []

        def fake_urlopen(req, timeout):
            captured_req.append(req)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            provider.complete("prompt")

        payload = json.loads(captured_req[0].data.decode())
        assert "system" not in payload

    def test_raises_runtime_error_on_url_error(self) -> None:
        from urllib.error import URLError

        provider = OllamaProvider()

        with patch("urllib.request.urlopen", side_effect=URLError("connection refused")):
            with pytest.raises(RuntimeError, match="Cannot reach Ollama"):
                provider.complete("prompt")

    def test_raises_runtime_error_on_generic_exception(self) -> None:
        provider = OllamaProvider()

        with patch("urllib.request.urlopen", side_effect=ValueError("unexpected")):
            with pytest.raises(RuntimeError, match="Ollama request failed"):
                provider.complete("prompt")

    def test_strips_whitespace_from_response(self) -> None:
        provider = OllamaProvider()
        mock_resp = self._make_response("  trimmed text  \n")

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = provider.complete("prompt")

        assert result == "trimmed text"
