# MEMORY.md — My Kaizen 프로젝트 메모리

> **목적:** 세션 간 컨텍스트 연속성. CLAUDE.md §7 정책에 따라 유지.
> **세션 시작 시:** 이 파일을 먼저 읽어 이전 컨텍스트를 파악한 후 작업 시작.

---

## 현재 상태

- **마지막 업데이트:** 2026-04-24
- **활성 브랜치:** `main`
- **마지막 커밋:** `3459fd3` (Sprint 4) → 추가 reduce 커밋 예정
- **모드:** Full (Speckit) — `specs/english_app_ux/` 완료 (일치율 95%)
- **미해결 이슈:**
  - NFR-3 (커버리지 ≥80%) — 55%로 미달, UI render 함수는 Streamlit AppTest harness 별도 이터레이션 필요

---

## 작업 이력 (최신순)

| 날짜 | 작업 | 세션 ID | 모드 | 커밋 | specs |
|------|------|--------|------|------|-------|
| 2026-04-23 ~ 04-24 | english_app UX/시인성/응답성 개선 (Sprint 1~4) | 43d310be | Full | 8b713f3 (1~3) + 3459fd3 (4) | `specs/english_app_ux/` |

---

## 알려진 이슈

- [x] ~~NFR-2 미달~~: 사이드바 + video_panel + fetch_video_info 추출로 **288 lines** 달성 ✅
- [ ] **NFR-3 미달**: pytest 커버리지 55% (목표 ≥80%). UI render 함수는 단위 테스트 어려움 → Streamlit AppTest harness 도입을 별도 이터레이션으로 분리.
- [ ] **FR-7 부분 충족**: URL 입력 시 `st.rerun()` 유지. blur/Enter 명시적 콜백 패턴 미적용. 캐시로 fetch 비용 0이라 사용자 체감은 양호.
- [ ] **S3-8 deferred**: History 테이블 `st.dataframe + on_select` 전환 — 다음 이터레이션 후보.

---

## 다음 이터레이션 후보 (Backlog)

1. **Streamlit AppTest harness 도입** → UI 커버리지 측정 → 진정한 ≥80% 달성
2. **사이드바 컴포넌트화** → `app.py` ≤300 도달 (선택)
3. **Phase 3 Step 7-10 UI 확장** (spec §4.2 보류 항목)
4. **History `st.dataframe + on_select`** (S3-8)
5. **모바일 반응형** (spec §4.2 out-of-scope)

---

## 핵심 운영 정보

- **테스트 실행:** `source kaizen-venv/bin/activate && pytest tests/english_app/ -v`
- **앱 실행:** `streamlit run english_app/app.py`
- **Ollama 엔드포인트:** `http://localhost:11434` (기본)
- **로컬 LLM 디폴트 모델:** `gemma4:26b` (17GB) / 보조: `gpt-oss:latest` (13GB)
- **세션 데이터 위치:** `english_app/data/sessions/` (gitignored)
- **세션 인덱스:** `english_app/data/sessions/_index.json` (자동 생성/갱신)

---

## CLAUDE.md 헌법 핵심 (요약)

- 모드: Lean (3파일 이하) / Full (다중 모듈) — 양방향 전환
- TDD: Red → Green → Refactor 필수
- Full 모드 산출물: `specs/<작업명>/{spec, plan, tasks, analyze, report}.md`
- 모델: Sonnet 4.6 (80%) / Opus 4.6 (20% 아키텍처 결정 시)
