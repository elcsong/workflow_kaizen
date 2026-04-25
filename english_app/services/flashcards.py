"""Flash Card 시스템 — SM-2 + Card 인덱스 + 마이그레이션.

순수 함수 (sm2_schedule, normalize_front, card_id_for, stagger_initial_due_dates,
select_today_queue) + 파일 I/O 함수 (rebuild_index, sync_session_cards,
load_due_cards) 분리.
"""
from __future__ import annotations

import json
import logging
import re
import string
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Final, Iterable, Iterator

logger = logging.getLogger(__name__)

INDEX_FILENAME: Final[str] = "_flashcards_index.json"

DAILY_NEW_CAP: Final[int] = 20
DAILY_REVIEW_CAP: Final[int] = 50

INITIAL_EASE: Final[float] = 2.5
EASE_FLOOR: Final[float] = 1.3

VOCAB_BANK: Final[str] = "vocabulary"
GRAMMAR_BANK: Final[str] = "grammar"

# 4단계 평가 → SM-2 q (0..5)
_RATING_TO_Q: Final[dict[int, int]] = {0: 1, 1: 3, 2: 4, 3: 5}


@dataclass(frozen=True)
class Card:
    """학습용 단일 카드. 출처 세션과 SM-2 상태를 함께 보관."""

    id: str
    session_id: str
    session_title: str
    bank: str  # "vocabulary" | "grammar"
    front: str
    meaning: str = ""
    example: str = ""
    quote: str = ""
    ease: float = INITIAL_EASE
    interval_days: int = 0
    reps: int = 0
    due_date: str = ""
    last_review: str = ""
    algorithm: str = "sm2"


# ---------- ID / 정규화 ----------

_PUNCT_RE = re.compile(r"[" + re.escape(string.punctuation) + r"]")
_WS_RE = re.compile(r"\s+")


def normalize_front(text: str) -> str:
    """카드 ID 안정화용 — lowercase + 공백 정규화 + 구두점 제거.

    "Neurobiological" / "neurobiological." / "  Neurobiological  "
    → 모두 "neurobiological" 로 수렴.
    """
    if not text:
        return ""
    cleaned = _PUNCT_RE.sub("", text.lower())
    cleaned = _WS_RE.sub(" ", cleaned).strip()
    return cleaned


def card_id_for(session_id: str, bank: str, front: str) -> str:
    """`{session_id}:{bank}:{normalize(front)}` 형태의 안정적 ID."""
    return f"{session_id}:{bank}:{normalize_front(front)}"


# ---------- SM-2 스케줄러 ----------

def sm2_schedule(card: Card, *, rating: int, today: date) -> Card:
    """SM-2 알고리즘으로 다음 복습 일정 계산.

    rating: 0(모름) | 1(어려움) | 2(좋음) | 3(쉬움)
    """
    if rating not in _RATING_TO_Q:
        raise ValueError(f"rating must be 0..3, got {rating}")
    q = _RATING_TO_Q[rating]

    if q < 3:  # 실패 — 처음부터 재학습
        new_reps = 0
        new_interval = 1
    else:
        new_reps = card.reps + 1
        if new_reps == 1:
            new_interval = 1
        elif new_reps == 2:
            new_interval = 6
        else:
            new_interval = max(1, round(card.interval_days * card.ease))

    new_ease = max(
        EASE_FLOOR,
        card.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)),
    )

    return replace(
        card,
        ease=new_ease,
        interval_days=new_interval,
        reps=new_reps,
        due_date=(today + timedelta(days=new_interval)).isoformat(),
        last_review=today.isoformat(),
    )


# ---------- 카드 추출 / 인덱스 빌드 ----------

def _make_card_from_vocab_row(session_id: str, session_title: str, row: dict) -> Card | None:
    word = (row.get("Word") or "").strip()
    if not word:
        return None
    return Card(
        id=card_id_for(session_id, VOCAB_BANK, word),
        session_id=session_id,
        session_title=session_title,
        bank=VOCAB_BANK,
        front=word,
        meaning=(row.get("Meaning") or "").strip(),
        example=(row.get("Example") or "").strip(),
        quote=(row.get("Quote") or row.get("quote") or "").strip(),
    )


def _make_card_from_grammar_row(session_id: str, session_title: str, row: dict) -> Card | None:
    pattern = (row.get("Sentence/Pattern") or "").strip()
    if not pattern:
        return None
    return Card(
        id=card_id_for(session_id, GRAMMAR_BANK, pattern),
        session_id=session_id,
        session_title=session_title,
        bank=GRAMMAR_BANK,
        front=pattern,
        meaning=(row.get("Grammar Point") or "").strip(),
        example=(row.get("Example") or "").strip(),
        quote=(row.get("Quote") or row.get("quote") or "").strip(),
    )


def _extract_cards_from_session(data: dict) -> Iterator[Card]:
    sid = data.get("id", "")
    if not sid:
        return
    title = data.get("video_title") or data.get("video_url", "")
    p2 = data.get("phase2", {}) or {}
    for row in p2.get("vocab_list") or []:
        card = _make_card_from_vocab_row(sid, title, row)
        if card:
            yield card
    for row in p2.get("grammar_list") or []:
        card = _make_card_from_grammar_row(sid, title, row)
        if card:
            yield card


def _index_path(review_dir: Path) -> Path:
    return review_dir / INDEX_FILENAME


def _read_index(review_dir: Path) -> list[Card]:
    path = _index_path(review_dir)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [Card(**item) for item in raw]
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("flashcards 인덱스 손상: %s", exc)
        return []


def _write_index(review_dir: Path, cards: Iterable[Card]) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    path = _index_path(review_dir)
    payload = [asdict(c) for c in cards]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rebuild_index(sessions_dir: Path, review_dir: Path) -> list[Card]:
    """모든 세션 JSON을 스캔해 카드 인덱스를 처음부터 재빌드.

    기존 review state(ease/interval/reps/due_date)는 ID 매칭으로 보존 시도.
    """
    existing = {c.id: c for c in _read_index(review_dir)}
    new_cards: list[Card] = []
    if sessions_dir.exists():
        for path in sorted(sessions_dir.iterdir()):
            if path.suffix != ".json" or path.name.startswith("_"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for card in _extract_cards_from_session(data):
                prior = existing.get(card.id)
                if prior is not None:
                    # 기존 review state 보존 + 콘텐츠는 최신으로 갱신
                    card = replace(
                        card,
                        ease=prior.ease,
                        interval_days=prior.interval_days,
                        reps=prior.reps,
                        due_date=prior.due_date,
                        last_review=prior.last_review,
                    )
                new_cards.append(card)

    _write_index(review_dir, new_cards)
    return new_cards


def sync_session_cards(sessions_dir: Path, review_dir: Path) -> list[Card]:
    """세션 변경(추가·삭제·편집)을 인덱스에 반영하고 orphan 제거.

    사실상 rebuild_index의 alias — 구현이 동일하므로 호출자 의도를 명확히
    하기 위한 별도 이름.
    """
    return rebuild_index(sessions_dir, review_dir)


# ---------- due 필터 / 큐 선택 ----------

def load_due_cards(
    review_dir: Path,
    *,
    today: date,
    session_id: str | None = None,
    bank: str | None = None,
) -> list[Card]:
    """오늘 또는 그 이전 due_date를 가진 카드 반환. 선택적으로 lecture/bank 필터."""
    cards = _read_index(review_dir)
    today_iso = today.isoformat()
    result: list[Card] = []
    for c in cards:
        if not c.due_date:
            continue
        if c.due_date > today_iso:
            continue
        if session_id and c.session_id != session_id:
            continue
        if bank and c.bank != bank:
            continue
        result.append(c)
    return result


def select_today_queue(
    candidates: list[Card],
    *,
    new_cap: int = DAILY_NEW_CAP,
    review_cap: int = DAILY_REVIEW_CAP,
) -> list[Card]:
    """오늘 학습 큐 — 신규 카드(reps==0)와 복습 카드(reps>0)에 각각 캡 적용."""
    new_cards = [c for c in candidates if c.reps == 0][:new_cap]
    review_cards = [c for c in candidates if c.reps > 0][:review_cap]
    # 신규 → 복습 순으로 노출
    return new_cards + review_cards


# ---------- 마이그레이션 ----------

def stagger_initial_due_dates(
    cards: list[Card],
    *,
    today: date,
    span_days: int = 7,
) -> list[Card]:
    """due_date가 비어있는 카드(=신규)에 created_at 기반 stagger 적용."""
    result: list[Card] = []
    for idx, card in enumerate(cards):
        if card.due_date:
            result.append(card)
            continue
        offset = idx % span_days
        result.append(replace(card, due_date=(today + timedelta(days=offset)).isoformat()))
    return result


# ---------- 통계 ----------

@dataclass(frozen=True)
class CardStats:
    total: int = 0
    new: int = 0  # reps==0
    learning: int = 0  # reps in 1..2
    mature: int = 0  # reps>=3
    due_today: int = 0


def compute_stats(cards: list[Card], *, today: date) -> CardStats:
    today_iso = today.isoformat()
    total = len(cards)
    new = sum(1 for c in cards if c.reps == 0)
    learning = sum(1 for c in cards if 1 <= c.reps <= 2)
    mature = sum(1 for c in cards if c.reps >= 3)
    due_today = sum(
        1 for c in cards if c.due_date and c.due_date <= today_iso
    )
    return CardStats(
        total=total, new=new, learning=learning, mature=mature, due_today=due_today,
    )


# ---------- 단일 카드 갱신 ----------

def upsert_card(review_dir: Path, card: Card) -> None:
    """리뷰 평가 후 단일 카드 상태를 인덱스에 반영."""
    cards = _read_index(review_dir)
    by_id = {c.id: c for c in cards}
    by_id[card.id] = card
    _write_index(review_dir, by_id.values())
