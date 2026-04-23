"""스트리밍 KPI 측정 유틸 — K1 (first token <1s), K3 (truncation 0%)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(frozen=True)
class StreamMetrics:
    first_token_seconds: float | None
    total_seconds: float
    chunk_count: int


def measure_first_token(chunks: Iterable[str]) -> Iterator[tuple[str, StreamMetrics]]:
    """스트림을 소비하며 첫 청크까지 걸린 시간을 함께 반환.

    첫 청크 수신 시점에 `(chunk, metrics_with_first_token_seconds)`를 emit,
    이후 청크는 `(chunk, metrics_without_update)` 반환 후 마지막에 총 시간 집계.
    """
    start = time.perf_counter()
    first_token_seconds: float | None = None
    count = 0
    for chunk in chunks:
        count += 1
        if first_token_seconds is None:
            first_token_seconds = time.perf_counter() - start
        yield chunk, StreamMetrics(
            first_token_seconds=first_token_seconds,
            total_seconds=time.perf_counter() - start,
            chunk_count=count,
        )
