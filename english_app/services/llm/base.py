"""LLM Provider 추상화와 공통 타입.

디자인 원칙:
- Protocol 기반 duck typing (Python 패턴 가이드 §Protocol).
- `stream()`은 `Iterator[str]`로 텍스트 청크만 반환 → `st.write_stream()`과 직접 호환.
- 종료 사유(finish/stop reason)는 스트림 소진 후 `get_last_finish_reason()`으로 조회 (KPI K3 검증용).
"""
from __future__ import annotations

from typing import Iterator, Protocol


class LLMProvider(Protocol):
    """모든 LLM Provider가 구현해야 하는 인터페이스."""

    name: str

    def list_models(self) -> list[str]:
        """Provider가 노출하는 모델 목록."""
        ...

    def is_available(self) -> bool:
        """Provider가 현재 사용 가능한 상태인지 (API 키·서버 기동 등)."""
        ...

    def stream(
        self,
        prompt: str,
        model: str,
        context: str | None = None,
    ) -> Iterator[str]:
        """텍스트 청크를 순차적으로 생성."""
        ...

    def get_last_finish_reason(self) -> str | None:
        """마지막 스트림의 종료 사유. truncation 0% 검증에 사용."""
        ...


class ProviderError(RuntimeError):
    """Provider 호출 중 복구 불가능한 오류."""


class ProviderUnavailable(ProviderError):
    """Provider가 사용 불가 상태 (API 키 없음·서버 꺼짐 등)."""
