"""OpenAI Provider — 스트리밍 재작성."""
from __future__ import annotations

import logging
import os
from typing import Iterator

from english_app.services.llm.base import ProviderUnavailable

logger = logging.getLogger(__name__)

DEFAULT_MODELS: tuple[str, ...] = (
    "gpt-5-mini-2025-08-07",
    "gpt-5.1-2025-11-13",
)


class OpenAIProvider:
    name = "OpenAI"

    def __init__(self, client=None, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = client  # 테스트 주입 지원
        self._last_finish_reason: str | None = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ProviderUnavailable("OPENAI_API_KEY 미설정")
        from openai import OpenAI  # lazy import

        self._client = OpenAI(api_key=self._api_key)
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
        messages: list[dict] = []
        if context:
            messages.append(
                {"role": "system", "content": f"Reference transcript:\n{context[:5000]}"}
            )
        messages.append({"role": "user", "content": prompt})

        client = self._get_client()
        try:
            stream = client.chat.completions.create(
                model=model, messages=messages, stream=True
            )
            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if choice is None:
                    continue
                delta = getattr(choice, "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    yield content
                finish = getattr(choice, "finish_reason", None)
                if finish:
                    self._last_finish_reason = finish
        except Exception as exc:
            logger.exception("OpenAI stream error")
            raise ProviderUnavailable(f"OpenAI 호출 실패: {exc}") from exc

    def get_last_finish_reason(self) -> str | None:
        return self._last_finish_reason
