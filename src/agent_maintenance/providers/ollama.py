"""Ollama LLM provider — local inference via the Ollama HTTP API.

No API key required. No extra pip dependencies.
Requires a locally running Ollama server (https://ollama.com).

Environment variables
---------------------
OLLAMA_HOST   Base URL of the Ollama server (default: http://localhost:11434).
OLLAMA_MODEL  Model name override (default: llama3.2).
"""

from __future__ import annotations

import json
import socket
import urllib.parse
import urllib.request
from urllib.error import URLError

from agent_maintenance.providers.base import LLMProvider

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2"


def reachable(base_url: str, timeout: float = 1.0) -> bool:
    """Return True if the Ollama TCP port is open — no HTTP request sent.

    Uses a raw socket connect so the check completes in at most *timeout* seconds
    even when Ollama is not running.
    """
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 11434
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class OllamaProvider(LLMProvider):
    """LLM provider backed by a locally running Ollama server.

    Sends a single, non-streaming POST to ``/api/generate`` and returns
    the completed text.  All network errors are converted to ``RuntimeError``
    with an actionable message so the rest of the pipeline stays clean.

    Args:
        base_url: Ollama server URL (default: ``http://localhost:11434``).
        model:    Model name to use (default: ``llama3.2``).
    """

    DEFAULT_HOST = _DEFAULT_HOST
    DEFAULT_MODEL = _DEFAULT_MODEL

    def __init__(
        self,
        base_url: str = _DEFAULT_HOST,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, prompt: str, *, system: str = "") -> str:
        """Send a completion request to the local Ollama server.

        Raises:
            RuntimeError: If Ollama is unreachable or returns an error.
        """
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("response", "").strip()
        except URLError as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {self._base_url}. "
                "Is the server running? Start it with: ollama serve\n"
                f"Underlying error: {exc}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Ollama request failed (model={self._model!r}): {exc}"
            ) from exc
