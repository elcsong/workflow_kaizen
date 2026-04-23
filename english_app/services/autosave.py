"""자동저장 정책 — Dirty 상태가 N초 이상 지속되면 저장 호출.

순수 의사결정 함수만 제공 (실제 저장은 호출자가 수행). 테스트 용이성 우선.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


DEFAULT_DEBOUNCE_SECONDS = 3.0


@dataclass(frozen=True)
class AutoSaveDecision:
    should_save: bool
    seconds_since_dirty: float


def should_autosave(
    *,
    is_dirty: bool,
    auto_save_enabled: bool,
    dirty_since: float | None,
    now: float | None = None,
    debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
) -> AutoSaveDecision:
    """자동저장이 필요한지 판정.

    - 자동저장 비활성·dirty 아님 → False
    - dirty_since가 None → 아직 dirty 시점 기록 안 됨 → False
    - 경과 시간 < debounce → False
    - 그 외 → True
    """
    if not (auto_save_enabled and is_dirty and dirty_since is not None):
        return AutoSaveDecision(False, 0.0)
    elapsed = (now or time.monotonic()) - dirty_since
    return AutoSaveDecision(elapsed >= debounce_seconds, elapsed)
