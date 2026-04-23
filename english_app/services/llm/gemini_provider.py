"""Gemini Provider — 스트리밍 재작성."""
from __future__ import annotations

import logging
import os
from typing import Iterator

from english_app.services.llm.base import ProviderUnavailable

logger = logging.getLogger(__name__)

DEFAULT_MODELS: tuple[str, ...] = (
    "gemini-2.5-pro",
    "gemini-2.5-flash",
)


class GeminiProvider:
    name = "Gemini"

    def __init__(self, model_factory=None, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._model_factory = model_factory  # 테스트 주입 지원
        self._last_finish_reason: str | None = None
        self._configured = False

    def _get_model(self, model_name: str):
        if self._model_factory is not None:
            return self._model_factory(model_name)
        if not self._api_key:
            raise ProviderUnavailable("GEMINI_API_KEY 미설정")
        import google.generativeai as genai  # lazy import

        if not self._configured:
            genai.configure(api_key=self._api_key)
            self._configured = True
        return genai.GenerativeModel(model_name)

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
        full_prompt = prompt if not context else (
            f"Reference transcript:\n{context[:5000]}\n\n---\n{prompt}"
        )

        try:
            gen_model = self._get_model(model)
            response_iter = gen_model.generate_content(full_prompt, stream=True)
            for chunk in response_iter:
                text = getattr(chunk, "text", None)
                if text:
                    yield text
            self._last_finish_reason = "stop"
        except ProviderUnavailable:
            raise
        except Exception as exc:
            logger.exception("Gemini stream error")
            raise ProviderUnavailable(f"Gemini 호출 실패: {exc}") from exc

    def get_last_finish_reason(self) -> str | None:
        return self._last_finish_reason
