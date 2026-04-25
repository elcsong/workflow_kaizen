"""Flash Card 시스템 — SM-2, Card ID, 인덱스, due 필터, stagger, orphan."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from english_app.services.flashcards import (
    DAILY_NEW_CAP,
    DAILY_REVIEW_CAP,
    Card,
    card_id_for,
    load_due_cards,
    normalize_front,
    rebuild_index,
    select_today_queue,
    sm2_schedule,
    stagger_initial_due_dates,
    sync_session_cards,
)


# ---------- normalize_front ----------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Neurobiological", "neurobiological"),
        ("  spaced  word  ", "spaced word"),
        ("Word.", "word"),
        ("Word!", "word"),
        ("not only X but also Y", "not only x but also y"),
    ],
)
def test_normalize_front_lowercases_and_strips(raw, expected):
    assert normalize_front(raw) == expected


def test_card_id_stable_across_capitalization():
    a = card_id_for("sess1", "vocabulary", "Neurobiological")
    b = card_id_for("sess1", "vocabulary", "neurobiological")
    assert a == b


def test_card_id_includes_bank_and_session():
    cid = card_id_for("sess1", "vocabulary", "abc")
    assert cid.startswith("sess1:vocabulary:")


# ---------- sm2_schedule ----------

def test_sm2_initial_correct_answer_schedules_one_day():
    today = date(2026, 4, 25)
    new_card = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
    )
    after = sm2_schedule(new_card, rating=2, today=today)  # 좋음
    assert after.reps == 1
    assert after.interval_days == 1
    assert after.due_date == "2026-04-26"
    assert after.last_review == today.isoformat()


def test_sm2_second_correct_schedules_six_days():
    today = date(2026, 4, 25)
    card = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
        reps=1, interval_days=1, ease=2.5,
    )
    after = sm2_schedule(card, rating=2, today=today)
    assert after.reps == 2
    assert after.interval_days == 6


def test_sm2_third_correct_uses_ease_factor():
    today = date(2026, 4, 25)
    card = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
        reps=2, interval_days=6, ease=2.5,
    )
    after = sm2_schedule(card, rating=2, today=today)
    assert after.reps == 3
    assert after.interval_days == 15  # round(6 * 2.5) = 15


def test_sm2_failure_resets_to_one_day():
    today = date(2026, 4, 25)
    card = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
        reps=5, interval_days=30, ease=2.5,
    )
    after = sm2_schedule(card, rating=0, today=today)  # 모름
    assert after.reps == 0
    assert after.interval_days == 1


def test_sm2_ease_floor_is_one_point_three():
    today = date(2026, 4, 25)
    card = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
        ease=1.4,
    )
    # 연속 모름으로 ease 깎이는데 1.3 미만으로 가지 않아야 함
    for _ in range(10):
        card = sm2_schedule(card, rating=0, today=today)
    assert card.ease >= 1.3


def test_sm2_easy_rating_increases_ease():
    today = date(2026, 4, 25)
    card = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
        ease=2.5,
    )
    after = sm2_schedule(card, rating=3, today=today)  # 쉬움
    assert after.ease > 2.5


# ---------- rebuild_index / sync_session_cards ----------

def _write_session(sessions_dir: Path, sid: str, *, vocab=(), grammar=(), title=""):
    payload = {
        "id": sid,
        "created_at": "2026-04-20T00:00:00",
        "video_url": "",
        "video_title": title,
        "phase1": {"notes": "", "missed_parts": ""},
        "phase2": {
            "vocab_issues": "", "grammar_issues": "", "linking_issues": "",
            "vocab_list": list(vocab),
            "grammar_list": list(grammar),
            "notes": "",
        },
        "phase3": {"audio_file": None, "summary": ""},
    }
    (sessions_dir / f"{sid}.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


def test_rebuild_index_aggregates_cards_from_all_sessions(tmp_path: Path):
    sdir = tmp_path / "sessions"
    sdir.mkdir()
    rdir = tmp_path / "review"
    _write_session(
        sdir, "20260101_000000", title="A",
        vocab=[{"Word": "alpha", "Meaning": "first", "Example": "ex"}],
        grammar=[{"Sentence/Pattern": "X but Y", "Grammar Point": "도치", "My Note": ""}],
    )
    _write_session(
        sdir, "20260102_000000", title="B",
        vocab=[{"Word": "beta", "Meaning": "second", "Example": ""}],
    )
    cards = rebuild_index(sdir, rdir)
    assert len(cards) == 3
    fronts = {c.front for c in cards}
    assert fronts == {"alpha", "X but Y", "beta"}


def test_rebuild_index_assigns_unique_ids(tmp_path: Path):
    sdir = tmp_path / "sessions"
    sdir.mkdir()
    _write_session(
        sdir, "s1",
        vocab=[{"Word": "alpha", "Meaning": "", "Example": ""}],
    )
    _write_session(
        sdir, "s2",
        vocab=[{"Word": "Alpha", "Meaning": "", "Example": ""}],  # 다른 세션 → 다른 ID
    )
    cards = rebuild_index(sdir, tmp_path / "review")
    ids = {c.id for c in cards}
    assert len(ids) == 2  # 다른 세션이므로 동일 단어라도 별개


def test_sync_removes_orphan_cards_when_session_deleted(tmp_path: Path):
    sdir = tmp_path / "sessions"
    sdir.mkdir()
    rdir = tmp_path / "review"
    _write_session(
        sdir, "s1", vocab=[{"Word": "alpha", "Meaning": "", "Example": ""}]
    )
    _write_session(
        sdir, "s2", vocab=[{"Word": "beta", "Meaning": "", "Example": ""}]
    )
    rebuild_index(sdir, rdir)

    # s2 세션 삭제
    (sdir / "s2.json").unlink()
    cards = sync_session_cards(sdir, rdir)
    assert {c.front for c in cards} == {"alpha"}


# ---------- load_due_cards ----------

def test_load_due_cards_returns_only_today_or_earlier(tmp_path: Path):
    sdir = tmp_path / "sessions"
    sdir.mkdir()
    rdir = tmp_path / "review"
    rdir.mkdir()
    today = date(2026, 4, 25)

    cards = [
        Card(id="a", session_id="s", session_title="t",
             bank="vocabulary", front="a", meaning="", example="", quote="",
             due_date="2026-04-24"),  # overdue
        Card(id="b", session_id="s", session_title="t",
             bank="vocabulary", front="b", meaning="", example="", quote="",
             due_date="2026-04-25"),  # today
        Card(id="c", session_id="s", session_title="t",
             bank="vocabulary", front="c", meaning="", example="", quote="",
             due_date="2026-04-26"),  # future
    ]
    rdir.mkdir(exist_ok=True)
    (rdir / "_flashcards_index.json").write_text(
        json.dumps([c.__dict__ for c in cards])
    )
    due = load_due_cards(rdir, today=today)
    fronts = {c.front for c in due}
    assert fronts == {"a", "b"}


def test_load_due_filters_by_bank(tmp_path: Path):
    rdir = tmp_path / "review"
    rdir.mkdir()
    today = date(2026, 4, 25)
    cards = [
        Card(id="a", session_id="s", session_title="t",
             bank="vocabulary", front="a", meaning="", example="", quote="",
             due_date="2026-04-25"),
        Card(id="b", session_id="s", session_title="t",
             bank="grammar", front="b", meaning="", example="", quote="",
             due_date="2026-04-25"),
    ]
    (rdir / "_flashcards_index.json").write_text(
        json.dumps([c.__dict__ for c in cards])
    )
    only_vocab = load_due_cards(rdir, today=today, bank="vocabulary")
    assert {c.front for c in only_vocab} == {"a"}


def test_load_due_filters_by_lecture(tmp_path: Path):
    rdir = tmp_path / "review"
    rdir.mkdir()
    today = date(2026, 4, 25)
    cards = [
        Card(id="a", session_id="s1", session_title="LectureA",
             bank="vocabulary", front="a", meaning="", example="", quote="",
             due_date="2026-04-25"),
        Card(id="b", session_id="s2", session_title="LectureB",
             bank="vocabulary", front="b", meaning="", example="", quote="",
             due_date="2026-04-25"),
    ]
    (rdir / "_flashcards_index.json").write_text(
        json.dumps([c.__dict__ for c in cards])
    )
    only_a = load_due_cards(rdir, today=today, session_id="s1")
    assert {c.front for c in only_a} == {"a"}


# ---------- stagger ----------

def test_stagger_distributes_initial_due_across_seven_days():
    today = date(2026, 4, 25)
    cards = [
        Card(id=f"id{i}", session_id="s", session_title="t",
             bank="vocabulary", front=f"w{i}",
             meaning="", example="", quote="")
        for i in range(14)
    ]
    staggered = stagger_initial_due_dates(cards, today=today, span_days=7)
    days = [date.fromisoformat(c.due_date) for c in staggered]
    distinct_days = sorted(set(days))
    # 7일 범위 안에 분포
    assert all(today <= d <= today + timedelta(days=6) for d in distinct_days)
    # 모든 카드가 due_date 보유
    assert all(c.due_date for c in staggered)


def test_stagger_skips_cards_already_scheduled():
    today = date(2026, 4, 25)
    scheduled = Card(
        id="x", session_id="s", session_title="t",
        bank="vocabulary", front="x", meaning="", example="", quote="",
        due_date="2026-05-01", reps=3,
    )
    new_card = Card(
        id="y", session_id="s", session_title="t",
        bank="vocabulary", front="y", meaning="", example="", quote="",
    )
    staggered = stagger_initial_due_dates([scheduled, new_card], today=today)
    assert staggered[0].due_date == "2026-05-01"  # 변경 X
    assert staggered[1].due_date  # 부여됨


# ---------- select_today_queue ----------

def test_select_today_queue_caps_new_and_review():
    today = date(2026, 4, 25)
    new_cards = [
        Card(id=f"n{i}", session_id="s", session_title="t",
             bank="vocabulary", front=f"n{i}",
             meaning="", example="", quote="",
             due_date=today.isoformat(), reps=0)
        for i in range(DAILY_NEW_CAP + 5)
    ]
    review_cards = [
        Card(id=f"r{i}", session_id="s", session_title="t",
             bank="vocabulary", front=f"r{i}",
             meaning="", example="", quote="",
             due_date=today.isoformat(), reps=3)
        for i in range(DAILY_REVIEW_CAP + 10)
    ]
    queue = select_today_queue(new_cards + review_cards)
    new_in_queue = [c for c in queue if c.reps == 0]
    review_in_queue = [c for c in queue if c.reps > 0]
    assert len(new_in_queue) == DAILY_NEW_CAP
    assert len(review_in_queue) == DAILY_REVIEW_CAP
