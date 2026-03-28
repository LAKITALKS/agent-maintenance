"""Anthropic Claude provider for LLM-assisted skill operations."""

from __future__ import annotations

from agent_maintenance.providers.base import LLMProvider

_INSTALL_HINT = (
    "anthropic SDK is not installed.\n"
    "To enable LLM-assisted merging, run:\n\n"
    "    pip install agent-maintenance[llm]\n"
)


class AnthropicProvider(LLMProvider):
    """LLM provider backed by Anthropic Claude via the official Python SDK.

    Requires:
        - pip install agent-maintenance[llm]
        - ANTHROPIC_API_KEY environment variable

    The provider is activated automatically by the factory when ANTHROPIC_API_KEY
    is set in the environment. No code changes are needed.
    """

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        try:
            import anthropic as _sdk
        except ImportError:
            raise ImportError(_INSTALL_HINT) from None

        if not api_key or not api_key.strip():
            raise ValueError(
                "ANTHROPIC_API_KEY is empty. "
                "Set the environment variable to a valid API key."
            )

        self._model = model
        self._sdk = _sdk
        self._client = _sdk.Anthropic(api_key=api_key)

    def complete(self, prompt: str, *, system: str = "") -> str:
        """Send a prompt to Claude and return the text response.

        Raises RuntimeError with a descriptive (non-sensitive) message on failure.
        The API key is never included in error messages or logs.
        """
        try:
            kwargs: dict = {
                "model": self._model,
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            response = self._client.messages.create(**kwargs)
            return response.content[0].text

        except self._sdk.AuthenticationError:
            raise RuntimeError(
                "Anthropic API authentication failed. "
                "Verify that ANTHROPIC_API_KEY is correct and active."
            ) from None

        except self._sdk.RateLimitError:
            raise RuntimeError(
                "Anthropic API rate limit exceeded. Wait a moment and try again."
            ) from None

        except self._sdk.APITimeoutError:
            raise RuntimeError(
                "Anthropic API request timed out. Check your network and retry."
            ) from None

        except self._sdk.APIStatusError as exc:
            raise RuntimeError(
                f"Anthropic API returned an error (HTTP {exc.status_code}). "
                "See https://docs.anthropic.com/en/api/errors for details."
            ) from None

        except self._sdk.APIError as exc:
            raise RuntimeError(f"Anthropic API error: {type(exc).__name__}") from exc

    def __repr__(self) -> str:
        return f"AnthropicProvider(model={self._model!r})"
