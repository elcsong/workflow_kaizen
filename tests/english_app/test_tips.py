"""TIPS 사전 — 6-Step 학습법의 모든 키 보유 확인."""
from __future__ import annotations

from english_app.ui.tips import TIPS

REQUIRED_KEYS = {
    "phase1",
    "phase2",
    "phase3",
    "p1_step2",
    "p1_step3",
    "p2_step5_vocab",
    "p2_step5_grammar",
    "p2_step5_linking",
    "p2_step5_notes",
    "p3_step9",
    "p3_step10",
}


def test_tips_dict_covers_all_steps():
    assert REQUIRED_KEYS <= set(TIPS.keys())


def test_tips_values_are_non_empty_strings():
    for key, value in TIPS.items():
        assert isinstance(value, str) and value.strip(), key
