# Gemini.md — My Kaizen 운영 헌법 (Antigravity Manifesto)

> **목적:** Antigravity(Gemini) 에이전트가 이 프로젝트에서 작업할 때 반드시 준수해야 할 규칙.
> **최종 갱신:** 2026-02-15

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | My Kaizen (workflow_kaizen) |
| **언어** | Python 3.9+ |
| **핵심 프레임워크** | Streamlit, FastAPI, Selenium |
| **데이터 처리** | pandas, numpy, BeautifulSoup4, lxml, xml.etree |
| **시각화** | plotly, matplotlib, seaborn |
| **AI/LLM** | google-generativeai, openai, anthropic |
| **NLP** | sentence-transformers (SBERT) |
| **PDF 처리** | pdfplumber, tabula-py, PyPDF2, camelot-py |
| **테스트 도구** | **pytest** |
| **린터/포매터** | black, flake8 |
| **DB** | SQLite3 (built-in) |
| **실행 환경** | macOS (launchd 스케줄링) |

### 주요 모듈 구조

```
my_kaizen/
├── modules/
│   ├── etl-pipeline/     # IEC62474·KOSHA·REACH 규제물질 ETL
│   ├── pdf-parser/       # 법령 PDF 파싱
│   └── visualization/    # Streamlit 대시보드
├── project/
│   └── intent_matcher/   # 의료장비 불량유형 판별 (CLI + Core + Scoring + Semantics)
├── english_app/          # 영어학습 Streamlit 앱
├── config/               # 환경 설정
├── scripts/              # 유틸리티 스크립트
└── docs/                 # 문서
```

---

## 2. 🧪 TDD (Test-Driven Development) Workflow

**모든 코드 변경은 반드시 아래 4단계 TDD 사이클을 따른다.**

### 2.1 TDD 4단계

| 단계 | 행동 | 확인 |
|------|------|------|
| **① RED** | 요구사항을 검증하는 **실패하는 테스트**를 먼저 작성 | `pytest` 실행 → FAIL 확인 |
| **② GREEN** | 테스트를 통과하는 **최소한의 코드**를 구현 | `pytest` 실행 → PASS 확인 |
| **③ REFACTOR** | 중복 제거, 네이밍 개선, 구조 정리 | `pytest` 실행 → 여전히 PASS |
| **④ COMMIT** | 변경사항 정리 및 문서 업데이트 | — |

### 2.2 테스트 컨벤션

```
tests/                         # 프로젝트 루트의 테스트 디렉토리
├── modules/
│   ├── test_iec62474_etl.py
│   ├── test_kosha_etl.py
│   └── test_reach_etl.py
├── intent_matcher/
│   ├── test_matcher.py
│   ├── test_hybrid_matcher.py
│   ├── test_keyword_extractor.py
│   └── test_scoring.py
├── english_app/
│   └── test_app_logic.py
└── conftest.py                # 공유 fixture
```

- **파일명:** `test_<모듈명>.py`
- **함수명:** `test_<기능>_<시나리오>_<기대결과>()`
- **fixture:** `conftest.py`에 공유 fixture 정의
- **실행 명령:** `pytest tests/ -v`
- **기존 코드 수정 시:** 관련 테스트가 없으면 **테스트 먼저 보강** 후 작업

### 2.3 테스트 우선순위

기존 코드 중 아래 기준으로 테스트 보강 우선순위를 결정:
1. **비즈니스 로직 밀도가 높은 파일** (파싱, 변환, 스코어링)
2. **외부 의존성이 많은 파일** (API, 웹 스크래핑 → mock 필수)
3. **파일 크기가 큰 모놀리식 파일** (단위 분리 후 테스트)

---

## 3. 💰 Token Efficiency & Context Management

### 3.1 파일 읽기 최소화
- `view_file_outline` → 구조 파악 우선, 필요한 함수만 `view_code_item`으로 열람
- **전체 파일을 통째로 읽지 않는다** (800줄 이상 파일 특히 주의)
- 작업과 **직접 관련 없는 파일은 분석에서 제외**

### 3.2 단계별 보고 (Plan → Approve → Execute)
- 코드 수정 전 **Implementation Plan**을 먼저 제안
- 사용자 승인을 받은 뒤에만 실행 단계로 진행
- 예상 변경 파일, 영향 범위, 테스트 계획을 포함

### 3.3 간결한 응답
- 코드 설명은 **소스 코드 주석**으로 대체
- 응답은 **실행 결과 위주로 요약**
- 불필요한 반복 설명 금지

### 3.4 컨텍스트 절약 원칙
- `kaizen-venv/` (가상환경)은 절대 탐색하지 않는다
- `data/`, `logs/` 디렉토리는 명시적 요청 없이 읽지 않는다
- 이전 대화에서 이미 분석한 내용은 KI(Knowledge Item)로 참조

---

## 4. 📋 작업 프로토콜

### 4.1 새 기능 추가 시
```
1. 요구사항 확인 → Implementation Plan 작성
2. 사용자 승인
3. 실패하는 테스트 작성 (RED)
4. 최소 구현 (GREEN)
5. 리팩토링 (REFACTOR)
6. pytest 전체 실행으로 회귀 확인
7. 완료 보고
```

### 4.2 버그 수정 시
```
1. 버그를 재현하는 테스트 작성 (RED)
2. 수정 (GREEN)
3. 관련 테스트 보강
4. 회귀 테스트 실행
```

### 4.3 리팩토링 시
```
1. 기존 동작을 검증하는 테스트가 있는지 확인
2. 없으면 보강 (characterization test)
3. 리팩토링 수행
4. 모든 테스트 PASS 확인
```

---

## 5. 🔒 금지 사항

- ❌ 테스트 없이 프로덕션 코드 수정
- ❌ `kaizen-venv/` 디렉토리 탐색 또는 수정
- ❌ 사용자 승인 없이 파일 삭제
- ❌ 전체 파일을 한번에 읽어서 토큰 낭비
- ❌ `.env`, API 키 등 민감 정보를 응답에 노출

---

## 6. 🛠 개발 환경 명령어 참조

```bash
# 가상환경 활성화
source kaizen-venv/bin/activate

# 테스트 실행
pytest tests/ -v

# 코드 포매팅
black .

# 린트 검사
flake8 .

# ETL 개별 실행 (예시)
python modules/etl-pipeline/iec62474_etl.py --help
```

---

## 7. 부록: 기술 스택 상세

| 카테고리 | 패키지 | 용도 |
|----------|--------|------|
| Web Scraping | selenium, webdriver-manager, beautifulsoup4 | ETL 데이터 수집 |
| Data | pandas, numpy | 데이터 처리/분석 |
| Visualization | streamlit, plotly, matplotlib, seaborn | 대시보드/차트 |
| API Framework | fastapi, uvicorn | REST API 서빙 |
| PDF | pdfplumber, tabula-py, PyPDF2, camelot-py | 법령 PDF 파싱 |
| AI/NLP | google-generativeai, openai, anthropic, sentence-transformers | LLM·임베딩 |
| Media | yt-dlp, youtube-transcript-api, imageio-ffmpeg | 영상/자막 처리 |
| Testing | pytest | 단위·통합 테스트 |
| Quality | black, flake8 | 코드 품질 |
| Scheduling | schedule, launchd (.plist) | 자동 실행 |
