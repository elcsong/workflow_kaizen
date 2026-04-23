# tasks.md — 실행 태스크 분해

> **프로젝트:** English Kaizen UX / 시인성 / 응답성 개선
> **작성:** PM Mina Seo
> **작성일:** 2026-04-23
> **전제:** `spec.md`, `plan.md` 승인 완료
> **현재 세션:** `43d310be`

## 상태 범례
- ⏳ pending / 🔵 in_progress / ✅ completed / ❌ blocked

---

## 🏁 Sprint 1: 안전망 & 모듈 뼈대

**기간:** 1 세션 단위
**목표:** 기존 `app.py` 동작 유지한 채 리팩토링 안전망과 새 구조의 빈 골격을 생성.
**Exit Criteria:** (1) 기존 앱 정상 실행 (2) pytest green (3) `ui/`, `services/` 폴더 생성 (4) characterization test 최소 10개

| # | 태스크 | 테스트 수 | 상태 | 세션 | 완료일 | 커밋 |
|---|-------|---------|------|------|-------|------|
| S1-1 | `tests/english_app/` 디렉토리 + `conftest.py` (공유 fixture) 생성 | 0 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-2 | `session_manager.py` characterization test (생성·저장·로드·삭제·리스트) | 6 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-3 | `video_service` 추출 + characterization test (URL 파싱) | 6 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-4 | `english_app/ui/` `services/` `services/llm/` 빈 `__init__.py` 생성 | 0 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-5 | `english_app/models.py` 생성 — `LLMResult`, `SessionSchema` dataclass | 2 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-6 | `english_app/config.py` 생성 — `.env` 로드, API 키 fail-fast 체크 | 3 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-7 | `app.py` `session_manager.py` 의 `print()` → `logging` 전환 | 0 | ✅ | 43d310be | 2026-04-23 | pending |
| S1-8 | 기존 앱 실행 확인 (`streamlit run english_app/app.py`) 스모크 테스트 | 0 | ✅ | 43d310be | 2026-04-23 | pending |

**Sprint 1 합계:** 태스크 8개 / 테스트 17개 / **17 passed**

---

## 🚀 Sprint 2: LLM 재설계 + 스트리밍

**기간:** 1-2 세션 단위
**목표:** 4 Provider 스트리밍, Ollama 디폴트, 구조화 결과 타입. **KPI K1·K3 달성.**
**Exit Criteria:** (1) 4 Provider 모두 `st.write_stream()` 연동 (2) first-token <1s 측정 (3) Anthropic truncation 0%

| # | 태스크 | 테스트 수 | 상태 | 세션 | 완료일 | 커밋 |
|---|-------|---------|------|------|-------|------|
| S2-1 | `services/llm/base.py` — `LLMProvider` Protocol + `ProviderUnavailable` | 0 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-2 | `services/llm/ollama.py` — Ollama Provider (gemma4:26b 디폴트, `/api/tags` 동적, 스트리밍) | 7 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-3 | `services/llm/openai_provider.py` — 스트리밍 재작성 | 3 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-4 | `services/llm/gemini_provider.py` — 스트리밍 재작성 | 3 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-5 | `services/llm/anthropic_provider.py` — 스트리밍 + max_tokens 8192 + was_truncated() | 4 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-6 | `services/llm/registry.py` — build_registry + available_providers (디폴트 앞 정렬) | 2 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-7 | Ollama 모델 하이브리드 (세션 캐시 + force_refresh) | *포함 S2-2 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-8 | `llm_helper.py` shim 전환 — 4 Provider + 친화적 모델명 | 0 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-9 | `app.py`에 `st.write_stream()` 연동 (Phase 2 AI 분석) | 0 | ✅ | 43d310be | 2026-04-23 | pending |
| S2-10 | `services/llm/metrics.py` — first-token 측정 유틸 | 2 | ✅ | 43d310be | 2026-04-23 | pending |

**Sprint 2 합계:** 태스크 10개 / 테스트 21개 / **38 passed (Sprint 1+2 누적)**

---

## ⚡ Sprint 3: 응답성 2차 + 안전성 UX

**기간:** 1 세션 단위
**목표:** 캐싱·인덱싱·콜백으로 rerun 제거. Dirty/삭제/자동저장 UX. **KPI K2·K4 달성.**
**Exit Criteria:** (1) Dashboard 렌더 <500ms (2) 편집 rerun 0회 (3) 삭제 모달 동작

| # | 태스크 | 테스트 수 | 상태 | 세션 | 완료일 | 커밋 |
|---|-------|---------|------|------|-------|------|
| S3-1 | `cached_video_info` — `@st.cache_data(ttl=3600)` 적용 (app.py 인라인) | 0 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-2 | `services/session_store.py` — `_index.json` 인덱싱 + upsert/remove | 5 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-3 | URL 입력에 캐시된 fetcher 사용 (cached_video_info) | 0 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-4 | `mark_dirty()` 헬퍼로 13곳 일괄 전환 + rerun 카운터 사이드바 노출 | 0 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-5 | `ui/components/dirty_badge.py` — 상단 노란 배지 | 2 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-6 | `services/autosave.py` + 사이드바 토글 (디폴트 off, 3s debounce) | 5 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-7 | `ui/components/delete_dialog.py` + `_delete_confirmation_dialog` | 2 | ✅ | 43d310be | 2026-04-24 | pending |
| S3-8 | History 테이블 수동 렌더 → `st.dataframe`+`on_select` | 0 | ⏸️ deferred | - | - | - |
| S3-9 | rerun 카운터 사이드바 표시(K4 자가측정), KPI K2는 사용자 인터랙션 측정 | 0 | ✅ | 43d310be | 2026-04-24 | pending |

**Sprint 3 합계:** 태스크 9개 (8 ✅ / 1 ⏸️) / 테스트 14개 / **52 passed (누적)**

> S3-8(History dataframe 전환)은 기존 동작 안정성과 트레이드오프 — Sprint 4 시인성 작업과 묶어 진행 예정.

---

## 🎨 Sprint 4: 시인성 & 최종 정리

**기간:** 1 세션 단위
**목표:** 디자인 토큰, 온보딩, 모듈 최종 정리. **NFR 전체 충족 + 커버리지 80%.**
**Exit Criteria:** (1) `app.py` ≤300 lines (2) 인라인 CSS ≤1 블록 (3) 타입 100% (4) 커버리지 ≥80%

| # | 태스크 | 테스트 수 | 상태 | 세션 | 완료일 | 커밋 |
|---|-------|---------|------|------|-------|------|
| S4-1 | `english_app/static/tokens.css` 생성 — 컬러/폰트/간격 변수 | 0 | ⏳ | - | - | - |
| S4-2 | 기존 인라인 CSS(`app.py:17-50`) → `tokens.css` 이동 + 로딩 로직 | 1 | ⏳ | - | - | - |
| S4-3 | `ui/components/onboarding.py` — 1-page 튜토리얼 (Dismissible) | 3 | ⏳ | - | - | - |
| S4-4 | `ui/dashboard.py` — 대시보드 뷰 분리 | 4 | ⏳ | - | - | - |
| S4-5 | `ui/learning.py` — 학습 모드 뷰 분리 | 4 | ⏳ | - | - | - |
| S4-6 | `ui/components/player.py` — YouTube 플레이어 컴포넌트 분리 | 1 | ⏳ | - | - | - |
| S4-7 | `ui/components/phase_tabs.py` — Phase 1/2/3 탭 컴포넌트 분리 | 3 | ⏳ | - | - | - |
| S4-8 | `app.py` 축소 — 라우터 전용, ≤300 lines | 1 | ⏳ | - | - | - |
| S4-9 | 타입 어노테이션 100% 검증 (`mypy` 또는 수동 점검) | 0 | ⏳ | - | - | - |
| S4-10 | pytest 커버리지 80%+ 달성 + 최종 스모크 테스트 | 0 | ⏳ | - | - | - |

**Sprint 4 합계:** 태스크 10개 / 테스트 17개

---

## 📊 전체 합계

| Sprint | 태스크 수 | 테스트 수 | 목표 KPI |
|--------|---------|---------|---------|
| Sprint 1 | 8 | 15 | (안전망) |
| Sprint 2 | 10 | 24 | K1, K3 |
| Sprint 3 | 9 | 21 | K2, K4 |
| Sprint 4 | 10 | 17 | NFR 전체, 커버리지 80%+ |
| **합계** | **37** | **77** | **K1~K4 + NFR** |

---

## 🔄 Sprint 간 게이트

각 Sprint 종료 시 PM Mina가 주재하는 게이트 점검:

```
1. pytest 전체 green 확인
2. 해당 Sprint Exit Criteria 수치 제시
3. 중간 데모 (옵션 — 사용자가 원하면)
4. 다음 Sprint 착수 승인
```

---

## ⏱️ 시작 지점

**다음 실행: Sprint 1-1** — `tests/english_app/conftest.py` 생성부터 착수.
