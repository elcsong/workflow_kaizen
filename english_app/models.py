"""공용 데이터 타입 — LLM 결과와 세션 스키마."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class LLMResult:
    """LLM 호출 결과의 불변 표현."""

    success: bool
    content: str
    provider: str
    model: str
    error: str | None = None
    truncated: bool = False


@dataclass(frozen=True)
class Phase1Data:
    notes: str = ""
    missed_parts: str = ""


@dataclass(frozen=True)
class Phase2Data:
    vocab_issues: str = ""
    grammar_issues: str = ""
    linking_issues: str = ""
    notes: str = ""
    vocab_list: tuple[dict, ...] = field(default_factory=tuple)
    grammar_list: tuple[dict, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Phase3Data:
    audio_file: str | None = None
    summary: str = ""


@dataclass(frozen=True)
class SessionSchema:
    """학습 세션의 구조화 스냅샷. 저장/로드 경계에서 사용."""

    id: str
    created_at: str
    video_url: str = ""
    video_title: str = ""
    phase1: Phase1Data = field(default_factory=Phase1Data)
    phase2: Phase2Data = field(default_factory=Phase2Data)
    phase3: Phase3Data = field(default_factory=Phase3Data)

    @staticmethod
    def new_id() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
