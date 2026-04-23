# plan.md — 구현 전략 및 토너먼트 설계

> **프로젝트:** English Kaizen UX / 시인성 / 응답성 개선
> **작성:** PM Mina Seo (토너먼트 주재)
> **작성일:** 2026-04-23
> **모드:** Full (Speckit)
> **전제:** `spec.md` 승인 완료

---

## 1. Context

`spec.md`에서 목표 G1~G5, KPI K1~K4, 스코프 In/Out이 확정되었다.
본 문서는 **아키텍처·구현 방식**을 결정하기 위해 두 개의 가상 팀이 서로 다른 접근으로 대안을 제출하고, Devil's Advocate(Kai)가 각 대안의 위험을 짚은 뒤, PM Mina가 최종 통합안을 제안한다.

### 해결해야 할 8가지 핵심 결정 (Tournament Scope)

| # | 결정 영역 | 선택지 |
|---|----------|-------|
| **D1** | 모듈 분해 순서 | (a) 전체 선(先) 분해 후 기능 추가 / (b) 기능별 점진적 분해 |
| **D2** | LLM Provider 추상화 | (a) `Protocol` (duck typing) / (b) `ABC` 상속 / (c) 함수 + registry dict |
| **D3** | LLM 스트리밍 통합 | (a) `st.write_stream()` 직접 / (b) 제너레이터 래퍼 + `st.empty()` 수동 렌더 |
| **D4** | Ollama 모델 리스트 | (a) 하드코드 + fallback / (b) `/api/tags` 런타임 동적 / (c) 하이브리드 (캐시 + 동적) |
| **D5** | 상태 관리 (Dirty·편집) | (a) `st.session_state` + `on_change` 콜백 / (b) 커스텀 `StateManager` 클래스 |
| **D6** | 리팩토링 안전망 | (a) characterization test 먼저 + 구현 / (b) TDD(test-first) 모듈 단위 신규 작성 |
| **D7** | 디자인 토큰 | (a) `static/tokens.css` 단일 파일 / (b) `theme/` 디렉토리 + 다크모드 지원 |
| **D8** | 자동 저장 | (a) Dirty 시 3초 debounce 후 자동 / (b) 수동 저장 + Dirty 배지 (자동 off) |

---

## 2. Team A — Performance-First (Alex · Hana)

**철학:** "동작하는 최소 골격을 먼저. 계측 가능한 KPI 달성이 최우선."

| 결정 | Team A 선택 | 근거 |
|------|-----------|------|
| **D1 모듈 분해** | **(b) 기능별 점진적 분해** | 큰 리팩토링은 회귀 리스크. 스트리밍·캐싱부터 꽂고, 안정화된 부분만 떼어냄 |
| **D2 추상화** | **(a) Protocol (duck typing)** | Python 패턴 규칙 준수(`typing.Protocol`). 상속 없이 가볍게 여러 Provider 대응 |
| **D3 스트리밍** | **(a) `st.write_stream()`** | 공식 API, 적은 코드, Streamlit 재실행 모델과 정합 |
| **D4 Ollama 모델** | **(c) 하이브리드** | 시작 시 `/api/tags` 1회 호출 → 세션에 캐시. 서버 미실행 시 빈 리스트 + 안내 |
| **D5 상태 관리** | **(a) `st.session_state` + `on_change` 콜백** | 새 구조 도입 비용 0, rerun 제거 효과 즉시 확인 가능 |
| **D6 안전망** | **(a) characterization test 먼저** | 기존 동작 고정 후 변경. 회귀 탐지 우선 |
| **D7 디자인 토큰** | **(a) 단일 `tokens.css`** | 개인 학습 툴이므로 다크모드는 YAGNI. 간결하게 |
| **D8 자동 저장** | **(b) 수동 + 배지** | 의도치 않은 저장 방지. 사용자 제어권 유지 |

### Team A 마일스톤 (4 Sprint)

```
Sprint 1 (안전망)        : characterization test 10+ 추가, session_store 인덱스, logging 전환
Sprint 2 (응답성 1차)     : LLM Protocol, Ollama Provider, 4 Provider 스트리밍, st.cache_data
Sprint 3 (응답성 2차·UX1) : on_change 콜백 전환, Dirty 배지, 삭제 모달
Sprint 4 (시인성·정리)    : tokens.css 분리, 온보딩, 최종 모듈 분해(ui/ 폴더), 커버리지 달성
```

### Team A 강점
- KPI K1~K4 조기 달성 (Sprint 2에 응답성 개선 완료)
- 회귀 리스크 최소 (characterization test 선행)
- 코드량 적음, 학습 곡선 낮음

### Team A 약점
- UX 재설계(Yuna가 지적한 P1 온보딩·P8 진행률)가 뒤로 밀림
- 모듈 분해가 점진적이라 중간 단계에서 "반만 분해된" 상태 존재

---

## 3. Team B — UX-First (Yuna · Jay)

**철학:** "사용자가 체감하는 흐름 전체를 먼저 재설계. 시인성과 일관성이 최우선."

| 결정 | Team B 선택 | 근거 |
|------|-----------|------|
| **D1 모듈 분해** | **(a) 전체 선(先) 분해** | `app.py` 840줄이 모든 변경의 걸림돌. 깨끗한 골격에서 UX 작업 필요 |
| **D2 추상화** | **(b) ABC 상속** | 명시적 인터페이스 문서화. IDE 자동완성·타입 체크 강함 |
| **D3 스트리밍** | **(b) 제너레이터 + `st.empty()`** | 스트리밍 중 상태 배지·로딩 애니메이션·취소 버튼 등 UX 레이어 커스터마이즈 |
| **D4 Ollama 모델** | **(b) 런타임 동적** | 사용자가 나중에 추가 설치한 모델도 자동 노출. 하드코드 유지 비용 0 |
| **D5 상태 관리** | **(b) 커스텀 `StateManager`** | Dirty·자동저장·온보딩 completed 등 UI 상태 일관성 확보 |
| **D6 안전망** | **(b) TDD 모듈 단위 신규 작성** | 분해 후 각 모듈은 신규 코드나 마찬가지. test-first로 시작 |
| **D7 디자인 토큰** | **(b) `theme/` + 다크모드** | 장시간 학습 피로도 완화. 토큰 한 번 정리 시 확장 용이 |
| **D8 자동 저장** | **(a) 3초 debounce 자동** | 사용자 인지 부하 ↓. Dirty 배지는 저장 직전 잠깐 노출 |

### Team B 마일스톤 (4 Sprint)

```
Sprint 1 (기반)          : 전체 모듈 분해 (ui/, services/, models.py), 타입 어노테이션, 로깅
Sprint 2 (LLM + 스트리밍)  : ABC LLMProvider, 4 Provider 구현, 제너레이터 래퍼
Sprint 3 (UX 재설계)      : 온보딩, Dirty 상태, 자동 저장, 삭제 모달, 진행률 세분화
Sprint 4 (시인성·다크모드) : theme/ 디자인 시스템, 라이트/다크 토글, 최종 테스트 보강
```

### Team B 강점
- UX 페인 P1~P10 대부분 커버
- 장기 유지보수성 우수 (깨끗한 초기 골격)
- 다크모드로 차별화된 학습 경험

### Team B 약점
- Sprint 1이 크고 위험 — 840줄 한 번에 분해 시 회귀 가능성
- YAGNI 위반 소지 (다크모드, 커스텀 StateManager)
- KPI K1 스트리밍 first-token 달성이 Sprint 2로 밀림

---

## 4. Devil's Advocate "Kai" — 평가

### Kai의 A팀 비판
> "점진적 분해는 '영원한 중간 단계'의 위험이 있다. Sprint 4에 모듈 분해가 남아있는데, Sprint 3까지 KPI 달성에 만족하면 분해가 유야무야 끝날 수 있다. **Sprint 1에 모듈 골격의 최소 뼈대(ui/, services/ 폴더와 진입점)를 먼저 만들고, 기존 코드를 이동시키는 방식이 안전하다.**"

### Kai의 B팀 비판
> "840줄 한 번에 분해는 `spec.md` §7 리스크 #3과 정면 충돌. characterization test가 Sprint 1 내부에 포함되지 않으면 회귀 탐지 불가. 또한 **다크모드는 개인 학습 툴의 YAGNI에 위배**된다 — 사용자가 요구하지 않은 기능. 커스텀 StateManager도 `st.session_state`의 dict 래퍼 수준이면 과설계."

### Kai의 교차 경고
- **D4 (Ollama 동적)**: A팀의 캐시 + B팀의 런타임 동적을 결합하지 않으면, 앱 실행 중 사용자가 `ollama pull` 한 모델이 반영되지 않는다. **세션당 1회 동적 조회 + 수동 새로고침 버튼**이 실용적.
- **D8 (자동 저장)**: A팀 수동 방식은 안전하지만 사용자가 까먹는다. B팀 자동 debounce는 실수로 덮어쓰기 위험. **초기 디폴트는 수동(사용자 요청)으로 가되, 토글로 자동 저장 활성화 가능하도록** 양쪽 모두 구현.
- **D6 (안전망)**: characterization test 없이 TDD 신규만으로 가면, 숨겨진 edge case(예: video_id 파싱 정규식)를 놓친다. **두 접근을 병행** — 서비스 레이어는 characterization, 신규 LLM Provider는 TDD.

---

## 5. PM Mina의 통합안 (Final Recommendation)

**기본 철학: A팀의 안전성과 B팀의 비전을 결합.** Kai의 비판을 수용해 YAGNI 위반은 제거.

| # | 결정 | **최종 선택** | 근거 |
|---|------|-----------|------|
| **D1** | 모듈 분해 | **Sprint 1에 뼈대만 생성 + 점진 이동** (A·B 절충) | Kai 제안 수용 |
| **D2** | 추상화 | **(a) Protocol** | Python 규칙 준수, 경량 |
| **D3** | 스트리밍 | **(a) `st.write_stream()`** | 공식 API 우선, 필요 시 Sprint 3에 UX 레이어 확장 |
| **D4** | Ollama 모델 | **(c) 하이브리드 + 수동 새로고침 버튼** | Kai 제안 수용 |
| **D5** | 상태 관리 | **(a) `st.session_state` + `on_change`** | YAGNI 기준 과설계 배제 |
| **D6** | 안전망 | **병행 접근** (Kai 제안) — 서비스 레이어 characterization + 신규 LLM TDD |
| **D7** | 디자인 토큰 | **(a) 단일 `tokens.css`** (다크모드 제외) | 개인 툴 YAGNI |
| **D8** | 자동 저장 | **디폴트 수동 + 토글로 자동 저장 가능** | Kai 제안 수용, 사용자 승인 선택지 반영 |

### 통합 마일스톤 (4 Sprint, 각 독립 PR 단위)

```
┌─────────────────────────────────────────────────────────────────┐
│ Sprint 1: 안전망 & 모듈 뼈대  (Hana · Tom 주도)                  │
├─────────────────────────────────────────────────────────────────┤
│  - characterization tests (video_service, session_store)         │
│  - ui/, services/, services/llm/, models.py 빈 골격 생성          │
│  - config.py — .env 로드 fail-fast, 로깅 전환                    │
│  - Exit criteria: 기존 app.py 실행 이상 없음, 테스트 통과         │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Sprint 2: LLM 재설계 + 스트리밍  (Alex 주도, Tom TDD 파트너)     │
├─────────────────────────────────────────────────────────────────┤
│  - LLMProvider Protocol (base.py)                               │
│  - Ollama Provider (gemma4:26b 디폴트, gpt-oss 보조, 동적+캐시)   │
│  - OpenAI / Gemini / Anthropic Provider 스트리밍 재작성          │
│  - st.write_stream() 연동, LLMResult dataclass                  │
│  - max_tokens 상향, 구조화 에러 처리                            │
│  - Exit criteria: K1 (<1s first token), K3 (truncation 0%) 달성 │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Sprint 3: 응답성 2차 + 안전성 UX  (Alex · Yuna 공동)             │
├─────────────────────────────────────────────────────────────────┤
│  - fetch_video_info에 @st.cache_data(ttl=3600)                  │
│  - list_sessions() → sessions/_index.json 인덱싱                │
│  - URL 입력 on_change 콜백으로 rerun 제거                        │
│  - Dirty 배지, 자동 저장 토글 (디폴트 off)                       │
│  - 삭제 확인 모달 (st.dialog)                                    │
│  - Exit criteria: K2 (<500ms dashboard), K4 (0 rerun) 달성       │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ Sprint 4: 시인성 & 최종 정리  (Jay · Yuna 주도)                  │
├─────────────────────────────────────────────────────────────────┤
│  - static/tokens.css (컬러/폰트/간격 토큰)                       │
│  - 인라인 CSS 제거, 버튼/카드 컴포넌트화                         │
│  - 온보딩 1-page 튜토리얼 (첫 진입만)                            │
│  - Step 4 3열 가독성 개선                                       │
│  - app.py 300줄 이하로 축소 (라우터 전용)                        │
│  - pytest 커버리지 80%+ 달성                                    │
│  - Exit criteria: NFR-1~7 전체 충족                             │
└─────────────────────────────────────────────────────────────────┘
```

### 각 Sprint 완료 게이트

각 Sprint 종료 시:
1. pytest 전체 green
2. 해당 Sprint Exit criteria 충족 증거 제시 (측정 수치)
3. 사용자에게 데모 + 피드백 수렴
4. 다음 Sprint 시작 전 필요 시 계획 조정

---

## 6. 주요 인터페이스 초안

### 6.1 `services/llm/base.py` (Protocol)

```python
from typing import Protocol, Iterator
from dataclasses import dataclass

@dataclass(frozen=True)
class LLMResult:
    success: bool
    content: str
    error: str | None
    provider: str
    model: str

class LLMProvider(Protocol):
    name: str
    available_models: list[str]
    def stream(self, prompt: str, model: str, context: str | None = None) -> Iterator[str]: ...
    def is_available(self) -> bool: ...
```

### 6.2 `services/llm/ollama.py` (신규, 디폴트)

```python
OLLAMA_ENDPOINT = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:26b"
FALLBACK_MODELS = ["gemma4:26b", "gpt-oss:latest"]  # 동적 검출 실패 시
```

### 6.3 상태 관리 키 (`st.session_state`)

```
manager                    # SessionManager (기존)
current_session            # 현재 편집 중 세션
page                       # "dashboard" | "learning"
is_dirty                   # 저장 필요 여부 (기존 + UI 노출)
auto_save_enabled          # 자동 저장 토글 (신규, 디폴트 False)
onboarding_dismissed       # 온보딩 튜토리얼 닫음 여부 (신규)
llm_provider               # 선택된 Provider
llm_model                  # 선택된 모델
ollama_models_cache        # /api/tags 응답 캐시
```

---

## 7. 리스크 및 완화 (spec.md §7 확장)

| 리스크 | 완화 |
|-------|------|
| Sprint 1 모듈 뼈대 생성 시 import 경로 꼬임 | 빈 골격 + 실제 코드 이동을 **2개 PR로 분리** |
| Ollama 서버 미실행 시 앱 시작 실패 | `is_available()` 체크 실패 시 Provider 리스트에서 제외, 클라우드 Provider로 자동 대체 |
| `st.cache_data` 오작동 (session_state 의존성) | 순수 함수 기반으로 분리 (`video_service.py`는 Streamlit 의존 없음) |
| 4 Provider 스트리밍 API가 제각각 | 공통 Protocol에서 `Iterator[str]` 형태로 통일. 각 Provider 어댑터가 변환 |
| characterization test 작성에 시간 과도 소요 | 핵심 2개 서비스(video, session)만 필수. UI 부분은 시각 테스트로 대체 |
| gemma4:26b 응답이 느려 KPI 체감 품질 저하 | 사용자가 런타임에 `gpt-oss:latest` 또는 Anthropic Haiku로 즉시 전환 가능. KPI는 first-token 기준이므로 달성 |

---

## 8. 성공 판정 (Exit Criteria — Sprint 4 종료 시)

- [ ] KPI K1 (AI first token <1s) — 4 Provider 모두 측정 로그 제시
- [ ] KPI K2 (Dashboard <500ms) — Streamlit 프로파일러 스크린샷
- [ ] KPI K3 (Truncation 0%) — Anthropic stop_reason 전수 검사 결과
- [ ] KPI K4 (편집 rerun 0회) — `st.session_state._rerun_count` 측정
- [ ] pytest 커버리지 ≥ 80% (english_app)
- [ ] `app.py` ≤ 300 lines
- [ ] 함수 타입 어노테이션 100%
- [ ] `print()` 0건 (logging 모듈 사용)
- [ ] 인라인 CSS 최소화 (`<style>` 블록 1개 이하)

---

## 9. 승인 체크리스트 (이 문서 → tasks.md 진입 전)

- [ ] 8개 결정사항 (D1~D8) 최종 선택 동의
- [ ] 4 Sprint 마일스톤 구성 동의
- [ ] 인터페이스 초안 (`LLMProvider` Protocol, session_state 키) 동의
- [ ] Sprint 1부터 즉시 시작 승인

---

## 10. 다음 단계

1. **사용자 승인 (본 문서)**
2. **`tasks.md`** — Sprint별 상세 태스크 분해. 컬럼: `태스크 | 테스트 수 | 상태 | 세션 | 완료일 | 커밋`
3. **구현 착수** — Sprint 1부터 순차 진행, 각 Sprint 종료 시 게이트 통과 확인
4. **`analyze.md`** — 전체 완료 후 spec 대비 일치율 검증
5. **`report.md`** — 최종 교훈 + MEMORY.md 갱신
