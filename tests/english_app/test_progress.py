"""진행도 계산 검증."""
from __future__ import annotations

from english_app.services.progress import get_progress_stats


def test_blank_session_phase1():
    label, pct, _ = get_progress_stats({})
    assert label == "Phase 1: Listening" and pct == 0


def test_only_notes_advances_to_phase2():
    label, pct, _ = get_progress_stats({"phase1": {"notes": "x"}})
    assert label == "Phase 2: Analysis" and pct == 33


def test_analysis_advances_to_phase3():
    label, pct, _ = get_progress_stats(
        {"phase1": {"notes": "x"}, "phase2": {"grammar_issues": "y"}}
    )
    assert label == "Phase 3: Output" and pct == 66


def test_full_completion():
    label, pct, _ = get_progress_stats(
        {
            "phase1": {"notes": "x"},
            "phase2": {"grammar_issues": "y"},
            "phase3": {"summary": "z"},
        }
    )
    assert label == "Completed" and pct == 100


def test_handles_none_phase_dicts():
    label, pct, _ = get_progress_stats(
        {"phase1": None, "phase2": None, "phase3": None}
    )
    assert pct == 0
