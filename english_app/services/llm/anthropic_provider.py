"""Anthropic Provider — 스트리밍 + max_tokens 상향으로 truncation 방지."""
from __future__ import annotations

import logging
import os
from typing import Iterator

from english_app.services.llm.base import ProviderUnavailable

logger = logging.getLogger(__name__)

DEFAULT_MODELS: tuple[str, ...] = (
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
)

DEFAULT_MAX_TOKENS = 8192


class AnthropicProvider:
    name = "Anthropic"

    def __init__(
        self,
        client=None,
        api_key: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        self._client = client
        self._max_tokens = max_tokens
        self._last_finish_reason: str | None = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ProviderUnavailable("CLAUDE_API_KEY 미설정")
        from anthropic import Anthropic  # lazy import

        self._client = Anthropic(api_key=self._api_key)
        return self._client

    def list_models(self) -> list[str]:
        return list(DEFAULT_MODELS)

    def is_available(self) -> bool:
        return bool(self._api_key)

    def stream(
        self,
        prompt: str,
        model: str,
        context: str | None = None,
    ) -> Iterator[str]:
        self._last_finish_reason = None
        system_parts: list[str] = []
        if context:
            system_parts.append(f"Reference transcript:\n{context[:5000]}")
        system = "\n\n".join(system_parts) if system_parts else None

        client = self._get_client()
        try:
            with client.messages.stream(
                model=model,
                max_tokens=self._max_tokens,
                system=system if system else "",
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text_chunk in stream.text_stream:
                    if text_chunk:
                        yield text_chunk
                final = stream.get_final_message()
                self._last_finish_reason = getattr(final, "stop_reason", None)
        except ProviderUnavailable:
            raise
        except Exception as exc:
            logger.exception("Anthropic stream error")
            raise ProviderUnavailable(f"Anthropic 호출 실패: {exc}") from exc

    def get_last_finish_reason(self) -> str | None:
        return self._last_finish_reason

    def was_truncated(self) -> bool:
        """KPI K3 검증: stop_reason이 end_turn이 아니면 truncation."""
        if self._last_finish_reason is None:
            return False
        return self._last_finish_reason not in {"end_turn", "stop_sequence"}
