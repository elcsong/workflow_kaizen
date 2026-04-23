# spec.md — English Kaizen UX / 시인성 / 응답성 개선

> **프로젝트:** `english_app/` 3축 개선
> **작성:** PM Mina Seo (공저: Yuna Kim, Alex Huang)
> **작성일:** 2026-04-23
> **모드:** Full (Speckit)
> **최종 승인자:** 사용자 (chikang)

---

## 1. 배경 (Why)

`english_app/`은 6-Step TED 청취 학습법을 구현한 개인 학습 툴이다.
현재 다음 문제로 학습 몰입도가 저해된다:

1. **응답성** — LLM 호출이 동기 블로킹(3-15초 "정지"), Anthropic max_tokens=1024로 잘림, 캐싱 0%.
2. **시인성** — 하드코드 컬러·인라인 CSS·일관성 없는 상태 피드백.
3. **UX** — URL 입력 즉시 rerun으로 흐름 끊김, 삭제 확인 없음, Dirty 상태 미노출.
4. **모델 선택 제약** — OpenAI/Gemini/Anthropic 클라우드 API만 지원 → 오프라인·비용·프라이버시 이슈.
5. **기술 부채** — `app.py` 840줄 모놀리식, 타입 어노테이션 부재, 테스트 0건.

---

## 2. 목표 (What)

### 2.1 사용자 목표 (Persona: 본인 1인 개인 학습자)

- 하루 30분 TED 영상 한 편으로 6-Step 사이클을 **끊김 없이** 완주한다.
- AI 튜터 분석을 **즉시(스트리밍)** 확인하며 학습한다.
- **오프라인·비용 걱정 없이** 로컬 모델로 기본 학습을 하고, 필요 시 클라우드 모델로 심화 분석한다.
- 내 노트가 **안전하게 저장**되고 있다는 확신을 가진다.

### 2.2 제품 목표

| # | 목표 | 측정 가능한 결과 |
|---|------|-----------------|
| G1 | **응답성 향상** | AI 분석 first token < 1s, 편집 rerun 0회, Dashboard 렌더 < 500ms |
| G2 | **LLM 선택권 확대** | Ollama 로컬 기본 + 3개 클라우드 Provider 총 4 Provider 런타임 전환 |
| G3 | **시인성 개선** | 디자인 토큰 CSS 분리, 상태 배지 노출, 일관된 피드백 |
| G4 | **안전성** | 삭제 확인 · Dirty 상태 시각화 · 자동 저장 옵션 |
| G5 | **유지보수성** | `app.py` 840줄 → 모듈 분해(각 < 300줄), 타입 어노테이션 100%, pytest 커버리지 80%+ |

---

## 3. 성공 지표 (KPI)

우선순위 KPI 4개는 모두 필수 달성 조건:

| # | KPI | 현재 추정 | 목표 | 측정 방법 |
|---|-----|---------|------|----------|
| **K1** | AI 분석 first token 표시 시간 | 3-15s | **< 1s** | `time.perf_counter()` 스트리밍 첫 청크까지 |
| **K2** | Dashboard 초기 렌더 (세션 20개) | ~1.5s | **< 500ms** | Streamlit 프로파일러 + 수동 측정 |
| **K3** | LLM 응답 truncation 비율 | ~15% | **0%** | Anthropic 응답 `stop_reason != "end_turn"` 카운트 |
| **K4** | 텍스트 편집 rerun 횟수 | 매 키 입력 | **0회** | `on_change` 콜백 전환 후 `st.session_state._rerun_count` 측정 |

보조 KPI:

- pytest 커버리지 ≥ 80% (english_app 범위)
- `app.py` 파일 라인 수 ≤ 300
- 모든 함수 타입 어노테이션 100%

---

## 4. 범위 (Scope)

### 4.1 포함 (In-Scope)

#### LLM Provider 확장
- **Ollama 로컬 Provider 신규 추가**
  - 디폴트 모델: **`gemma4:26b`** (현재 설치 확인, 17GB)
  - 보조 모델: **`gpt-oss:latest`** (현재 설치 확인, 13GB)
  - 추가 설치 모델은 `ollama list` 런타임 동적 검출로 자동 노출 (plan.md에서 하드코드 vs 동적 검출 최종 결정)
  - 엔드포인트: `http://localhost:11434` (Ollama 기본)
  - 설치/미실행 안내 문구 포함 (FR-4)
- **기존 3 Provider 유지**: OpenAI, Gemini, Anthropic
- **Provider 디폴트 = Ollama** (오프라인 우선, 비용 0, 프라이버시)
- **스트리밍 필수** — 4 Provider 모두 스트리밍 응답
- **max_tokens 동적 설정** — 분석 용도 8192 권장, Provider별 상한 반영
- **구조화된 결과 타입** — `@dataclass(frozen=True) LLMResult{success, content, error, provider, model}`
- **API 키 시작 시 fail-fast 검증** + `.env` 로드

#### 응답성
- `@st.cache_data(ttl=3600)` 적용: `fetch_video_info`, `list_sessions`
- 세션 리스트 인덱싱: `sessions/_index.json` 메타데이터 파일
- URL 입력 `on_change` 콜백 전환 (rerun 최소화)
- `list_sessions()` 전체 파일 스캔 제거

#### 시인성 (UX·Visual)
- 디자인 토큰 CSS 파일 분리: `english_app/static/tokens.css`
- 컬러/폰트/간격 변수화 (`--color-*`, `--space-*`, `--text-*`)
- Dirty 상태 글로벌 배지 (상단 고정 "● Unsaved changes")
- 자동 저장 토글 (옵션, 디폴트 off)
- 삭제 확인 모달 (`st.dialog`)
- 온보딩 1-page 튜토리얼 (Dismissible, 첫 진입 시만)
- Step 4 3열 레이아웃 가독성 개선

#### 기술 부채 상환
- `app.py` 840줄 → 다음 모듈로 분해:
  - `english_app/ui/dashboard.py`
  - `english_app/ui/learning.py`
  - `english_app/ui/components/` (player, tabs, cards)
  - `english_app/services/video.py` (yt-dlp + transcript)
  - `english_app/services/llm.py` (기존 `llm_helper.py` 확장)
  - `english_app/models.py` (dataclass)
  - `english_app/app.py` ≤ 300줄 (라우팅만)
- 타입 어노테이션 100%
- `print()` → `logging` 모듈 전환
- pytest 테스트 신규 작성 (tests/english_app/)

### 4.2 제외 (Out-of-Scope)

- **Phase 3 Step 7-10 UI 신규 확장** — 이번엔 기존 수준 유지 (다음 이터레이션)
- **모바일 네이티브 반응형** — 데스크톱 브라우저 기준만 최적화
- **커스텀 YouTube 플레이어 재작성** — 기존 iframe 유지, rerun 시 상태 유실 이슈는 모니터링만
- **다국어 UI** — 한국어 UI 그대로
- **배포 자동화** — 로컬 실행만 지원

---

## 5. 요구사항 (Requirements)

### 5.1 기능 요구사항 (FR)

| ID | 요구사항 | 수용 기준 (Acceptance Criteria) |
|----|---------|-------------------------------|
| **FR-1** | 사용자는 사이드바에서 LLM Provider를 4개 중 선택할 수 있다 | Ollama, OpenAI, Gemini, Anthropic 드롭다운 노출. 디폴트 Ollama. |
| **FR-2** | 사용자는 Provider별 모델을 선택할 수 있다 | Ollama: **gemma4:26b(디폴트)**, gpt-oss:latest + `ollama list` 동적 검출로 추가 모델 자동 노출 / 기존 Provider 모델 유지 |
| **FR-3** | AI 분석 응답이 스트리밍으로 실시간 표시된다 | first token < 1s. `st.write_stream()` 사용 |
| **FR-4** | Ollama 미실행 시 명확한 안내가 노출된다 | "Ollama 서버가 실행되지 않았습니다. `ollama serve` 실행 후 다시 시도하세요." |
| **FR-5** | 세션 저장되지 않은 변경사항이 시각적으로 표시된다 | 상단에 "● Unsaved changes" 배지. 저장 후 사라짐 |
| **FR-6** | 세션 삭제 시 확인 모달이 나타난다 | `st.dialog` 모달. "삭제하시겠습니까?" + 취소 가능 |
| **FR-7** | URL 입력 중 편집이 끊기지 않는다 | 입력 중 rerun 0회. blur/Enter 시에만 fetch |
| **FR-8** | 대시보드가 500ms 이내에 렌더된다 | 세션 20개 기준 측정. 인덱싱으로 달성 |

### 5.2 비기능 요구사항 (NFR)

| ID | 요구사항 |
|----|---------|
| **NFR-1** | 모든 함수에 타입 어노테이션 (Python 3.9+ 문법) |
| **NFR-2** | `app.py`는 라우팅만 담당하며 300줄 이하 |
| **NFR-3** | pytest 커버리지 80% 이상 (english_app 범위) |
| **NFR-4** | 모든 LLM Provider 모듈은 `LLMProvider` Protocol 준수 |
| **NFR-5** | API 키는 `.env`에서 로드, 누락 시 앱 시작 시점에 경고 |
| **NFR-6** | 로깅은 `logging` 모듈 사용 (print 금지) |
| **NFR-7** | CSS는 `static/tokens.css`로 분리, 인라인 CSS 최소화 |

---

## 6. 아키텍처 방향 (High-Level)

> 구체 설계는 `plan.md`에서 토너먼트로 결정.

```
english_app/
├── app.py                      # 라우터 전용 (≤ 300 lines)
├── models.py                   # LLMResult, SessionSchema 등 dataclass
├── config.py                   # .env 로드, 상수
├── ui/
│   ├── dashboard.py            # 대시보드 뷰
│   ├── learning.py             # 학습 모드 뷰
│   └── components/
│       ├── player.py           # YouTube 플레이어
│       ├── phase_tabs.py       # Phase 1/2/3 탭
│       ├── dirty_badge.py      # 저장 상태 배지
│       └── onboarding.py       # 신규 사용자 튜토리얼
├── services/
│   ├── video.py                # yt-dlp + transcript (캐시됨)
│   ├── session_store.py        # 세션 I/O + 인덱싱
│   └── llm/
│       ├── base.py             # LLMProvider Protocol
│       ├── ollama.py           # Ollama (NEW, 디폴트)
│       ├── openai.py
│       ├── gemini.py
│       └── anthropic.py
├── static/
│   └── tokens.css              # 디자인 토큰
└── data/                       # (기존 유지)

tests/english_app/
├── test_session_store.py
├── test_video_service.py
├── test_llm_providers.py
└── test_dashboard_render.py
```

---

## 7. 리스크 및 완화

| 리스크 | 완화책 |
|-------|------|
| Ollama 로컬 미설치 사용자 → 디폴트가 실패 | FR-4 안내 문구 + README에 설치 가이드 |
| 스트리밍 전환이 Streamlit 콜백과 충돌 | `st.write_stream()` 공식 API 사용, 프로토타입 먼저 검증 |
| 840줄 리팩토링 중 회귀 발생 | Tom(QA)이 **characterization test** 먼저 보강 (현 동작 고정) 후 분해 |
| gemma4:26b 토큰 속도가 느림(26B 파라미터) → 전체 응답 완료 시간 증가 | first-token KPI(K1 <1s)는 **스트리밍**으로 달성. 총 완료 시간 지연은 허용(사용자 선택). 속도 우선 시 `gpt-oss:latest` 또는 클라우드 Provider로 런타임 전환 |
| 로컬 모델 응답 품질이 GPT-5/Claude 4.5 대비 낮음 | 사용자 선택권 보존. 심화 분석 시 클라우드 Provider 전환 가능 |
| KPI K2 (Dashboard 500ms) 달성 난이도 | 세션 수 증가 시 재측정 주기 필요 — `_index.json` 전략이 충분한지 plan에서 검증 |

---

## 8. 승인 체크리스트 (ExitPlanMode 전 확인)

사용자가 아래 항목에 확인하면 `plan.md` 단계로 진입:

- [ ] 목표 G1~G5 동의
- [ ] KPI K1~K4 동의 (모두 필수)
- [ ] 스코프 In/Out 동의
  - [ ] Ollama + **gemma4:26b** 디폴트 확정 (보조: gpt-oss:latest, 동적 검출)
  - [ ] 제외 항목(Phase 3 확장, 모바일, 플레이어 재작성, 다국어, 배포) 동의
- [ ] 아키텍처 방향(모듈 분해 구조) 동의
- [ ] 리스크 완화책 동의

---

## 9. 다음 단계

1. **사용자 승인 (본 문서)**
2. **`plan.md`** — 토너먼트 설계 (팀 A vs 팀 B 구현 접근), Kai(Devil's Advocate) 평가
3. **`tasks.md`** — 세부 태스크 분해 (테스트 수 포함)
4. **구현** (TDD: Red → Green → Refactor)
5. **`analyze.md`** — spec 대비 일치율 검증
6. **`report.md`** — 최종 결과 + 교훈 + MEMORY.md 갱신
