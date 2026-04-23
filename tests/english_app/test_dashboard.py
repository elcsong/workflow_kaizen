"""대시보드 보강 함수 검증 (rendering은 직접 테스트하지 않고 데이터 변환만)."""
from __future__ import annotations

from english_app.ui.dashboard import _enrich_with_stage


def test_enrich_uses_provided_stage_label():
    sessions = [
        {
            "id": "a",
            "created_at": "2026-04-24",
            "stage_label": "Phase 2: Analysis",
            "progress_pct": 33,
        }
    ]
    enriched, completed, in_progress = _enrich_with_stage(sessions)
    assert enriched[0]["icon"] == "📝"
    assert (completed, in_progress) == (0, 1)


def test_enrich_calculates_when_missing():
    sessions = [
        {
            "id": "a",
            "created_at": "2026-04-24",
            "phase1": {"notes": "x"},
            "phase2": {"grammar_issues": "y"},
            "phase3": {"summary": "z"},
        }
    ]
    enriched, completed, in_progress = _enrich_with_stage(sessions)
    assert enriched[0]["stage_label"] == "Completed"
    assert enriched[0]["progress_pct"] == 100
    assert (completed, in_progress) == (1, 0)


def test_enrich_handles_empty_list():
    enriched, completed, in_progress = _enrich_with_stage([])
    assert enriched == []
    assert (completed, in_progress) == (0, 0)
