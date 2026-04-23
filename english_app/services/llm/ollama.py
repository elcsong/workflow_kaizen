"""Ollama 로컬 Provider.

- 디폴트: `gemma4:26b` (사용자 설치 기준)
- 엔드포인트: 기본 `http://localhost:11434` (OLLAMA_HOST 환경변수 오버라이드)
- 모델 목록: `/api/tags`로 런타임 조회 + 세션 캐시
- 스트리밍: `/api/chat`의 NDJSON 응답을 순차 파싱
"""
from __future__ import annotations

import json
import logging
from typing import Iterator

import requests

from english_app.config import (
    OLLAMA_DEFAULT_MODEL,
    OLLAMA_ENDPOINT,
    OLLAMA_FALLBACK_MODELS,
)
from english_app.services.llm.base import ProviderUnavailable

logger = logging.getLogger(__name__)

_TAG_TIMEOUT = 2.0
_STREAM_TIMEOUT = 120.0


class OllamaProvider:
    """Ollama 로컬 Provider 구현체."""

    name = "Ollama"

    def __init__(
        self,
        endpoint: str = OLLAMA_ENDPOINT,
        default_model: str = OLLAMA_DEFAULT_MODEL,
        session: requests.Session | None = None,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.default_model = default_model
        self._session = session or requests.Session()
        self._last_finish_reason: str | None = None
        self._models_cache: list[str] | None = None

    def list_models(self, force_refresh: bool = False) -> list[str]:
        """`/api/tags` 호출로 설치된 모델 목록을 조회. 실패 시 fallback 반환."""
        if self._models_cache is not None and not force_refresh:
            return self._models_cache
        try:
            resp = self._session.get(
                f"{self.endpoint}/api/tags", timeout=_TAG_TIMEOUT
            )
            resp.raise_for_status()
            payload = resp.json()
            models = [m["name"] for m in payload.get("models", [])]
            # 디폴트 모델을 맨 앞으로
            models.sort(key=lambda n: 0 if n == self.default_model else 1)
            self._models_cache = models or list(OLLAMA_FALLBACK_MODELS)
            return self._models_cache
        except (requests.RequestException, ValueError, KeyError) as exc:
            logger.warning("Ollama /api/tags 조회 실패: %s — fallback 사용", exc)
            self._models_cache = list(OLLAMA_FALLBACK_MODELS)
            return self._models_cache

    def is_available(self) -> bool:
        try:
            resp = self._session.get(f"{self.endpoint}/", timeout=_TAG_TIMEOUT)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def stream(
        self,
        prompt: str,
        model: str,
        context: str | None = None,
    ) -> Iterator[str]:
        """`/api/chat` 스트리밍 엔드포인트 호출."""
        self._last_finish_reason = None
        messages: list[dict] = []
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Reference transcript:\n{context[:5000]}",
                }
            )
        messages.append({"role": "user", "content": prompt})

        try:
            with self._session.post(
                f"{self.endpoint}/api/chat",
                json={"model": model, "messages": messages, "stream": True},
                stream=True,
                timeout=_STREAM_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    try:
                        chunk = json.loads(raw_line)
                    except json.JSONDecodeError:
                        logger.debug("Ollama 비정상 라인 무시: %r", raw_line)
                        continue
                    if chunk.get("done"):
                        self._last_finish_reason = chunk.get("done_reason", "stop")
                        break
                    content = chunk.get("message", {}).get("content")
                    if content:
                        yield content
        except requests.RequestException as exc:
            raise ProviderUnavailable(
                f"Ollama 요청 실패 ({self.endpoint}): {exc}"
            ) from exc

    def get_last_finish_reason(self) -> str | None:
        return self._last_finish_reason
