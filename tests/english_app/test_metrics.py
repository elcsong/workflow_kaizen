"""KPI 측정 유틸 — first-token 타이밍 검증."""
from __future__ import annotations

import time

from english_app.services.llm.metrics import measure_first_token


def test_first_token_latency_under_threshold():
    def _gen():
        yield "a"
        time.sleep(0.01)
        yield "b"

    results = list(measure_first_token(_gen()))
    assert len(results) == 2
    _, m0 = results[0]
    assert m0.first_token_seconds is not None
    assert m0.first_token_seconds < 0.5
    _, m_final = results[-1]
    assert m_final.chunk_count == 2


def test_first_token_none_when_empty_stream():
    results = list(measure_first_token(iter([])))
    assert results == []
