"""세션 저장소 — `sessions/_index.json` 메타데이터 인덱싱.

Sprint 1의 `session_manager.py`는 매 호출마다 모든 JSON 파일을 열어 파싱했다.
세션이 100개를 넘으면 대시보드 렌더가 느려진다(KPI K2 위반).
본 모듈은 가벼운 인덱스 파일만 유지하여 목록 조회를 O(1)로 만든다.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

INDEX_FILENAME = "_index.json"


@dataclass(frozen=True)
class SessionIndexEntry:
    id: str
    created_at: str
    video_url: str = ""
    video_title: str = ""
    stage_label: str = ""
    progress_pct: int = 0


def _index_path(sessions_dir: Path) -> Path:
    return sessions_dir / INDEX_FILENAME


def load_index(sessions_dir: Path) -> list[SessionIndexEntry]:
    """인덱스 파일이 있으면 그것만 읽어 빠르게 반환."""
    path = _index_path(sessions_dir)
    if not path.exists():
        return rebuild_index(sessions_dir)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [SessionIndexEntry(**item) for item in raw]
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("인덱스 손상, 재빌드: %s", exc)
        return rebuild_index(sessions_dir)


def rebuild_index(sessions_dir: Path) -> list[SessionIndexEntry]:
    """모든 세션 JSON을 스캔해 인덱스를 재생성하고 디스크에 저장."""
    if not sessions_dir.exists():
        return []
    entries: list[SessionIndexEntry] = []
    for path in sessions_dir.iterdir():
        if path.name == INDEX_FILENAME or path.suffix != ".json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entries.append(_entry_from_session(data))
    entries.sort(key=lambda e: e.created_at, reverse=True)
    save_index(sessions_dir, entries)
    return entries


def save_index(
    sessions_dir: Path, entries: Iterable[SessionIndexEntry]
) -> None:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    path = _index_path(sessions_dir)
    payload = [asdict(e) for e in entries]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_entry(sessions_dir: Path, session_data: dict) -> None:
    """단일 세션 변경을 인덱스에 반영 (저장 후 호출)."""
    entries = load_index(sessions_dir)
    new_entry = _entry_from_session(session_data)
    by_id = {e.id: e for e in entries}
    by_id[new_entry.id] = new_entry
    sorted_entries = sorted(by_id.values(), key=lambda e: e.created_at, reverse=True)
    save_index(sessions_dir, sorted_entries)


def remove_entry(sessions_dir: Path, session_id: str) -> None:
    entries = [e for e in load_index(sessions_dir) if e.id != session_id]
    save_index(sessions_dir, entries)


def _entry_from_session(data: dict) -> SessionIndexEntry:
    p1 = data.get("phase1", {}) or {}
    p2 = data.get("phase2", {}) or {}
    p3 = data.get("phase3", {}) or {}
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
        stage, pct = "Completed", 100
    elif has_analysis:
        stage, pct = "Phase 3: Output", 66
    elif has_notes:
        stage, pct = "Phase 2: Analysis", 33
    else:
        stage, pct = "Phase 1: Listening", 0

    return SessionIndexEntry(
        id=data.get("id", ""),
        created_at=data.get("created_at", ""),
        video_url=data.get("video_url", ""),
        video_title=data.get("video_title", ""),
        stage_label=stage,
        progress_pct=pct,
    )
