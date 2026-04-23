"""세션 진행도 계산 — Phase 1/2/3 완료 여부에서 단계 라벨/퍼센트 도출."""
from __future__ import annotations

from typing import Mapping


def get_progress_stats(session: Mapping) -> tuple[str, int, str]:
    """(stage_label, progress_pct, icon) 반환."""
    p1 = session.get("phase1", {}) or {}
    p2 = session.get("phase2", {}) or {}
    p3 = session.get("phase3", {}) or {}

    has_notes = bool(p1.get("notes") or p1.get("missed_parts"))
    has_analysis = bool(
        p2.get("vocab_issues")
        or p2.get("grammar_issues")
        or p2.get("linking_issues")
        or p2.get("vocab_list")
        or p2.get("grammar_list")
    )
    has_output = bool(p3.get("summary") or p3.get("audio_file"))

    if has_notes and has_analysis and has_output:
        return "Completed", 100, "✅"
    if has_analysis:
        return "Phase 3: Output", 66, "🗣️"
    if has_notes:
        return "Phase 2: Analysis", 33, "📝"
    return "Phase 1: Listening", 0, "👂"
