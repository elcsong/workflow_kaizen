# my Workflow Kaizen

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

## 📘 Project Overview
Workflow Kaizen is my personal project for enhancing work efficiency through automation, ETL processes, and data analysis. The goal is to automate tedious manual tasks, reduce human errors, and speed up workflows using Python and AI tools like Cursor. This repository serves as a portfolio to showcase my self-taught skills in data engineering and automation.

**🚀 Current Focus**: Building robust ETL pipelines for chemical safety data from international and domestic regulatory bodies, demonstrating end-to-end data engineering capabilities.

All projects here use general external data sources only—no company-internal data is involved.

## 👋 Hey there, I'm LazyButSmart!
안녕하세요! 저는 "게으르지만 똑똑하게" 일하는 걸 모토로 사는 평범한 회사원이에요. 😎 비전공자 출신이지만, 운명의 장난처럼 첫 직장에서 품질 업무에 빠져들었고, 지금까지 그 길을 걷고 있어요. 현재는 의료기기 회사 연구소에서 품질 담당자로 일하며, 매일매일 데이터와 씨름 중입니다. "필요는 발명의 어머니"라고 하잖아요? 그래서 혼자서 데이터 엔지니어링과 분석을 공부하며 Python을 무기로 삼았어요. (Python이 제 커피만큼 소중해요 ☕)

## 🚀 My Wild Journey
완전 비전공자에서 시작해서, 품질 체크리스트와 엑셀 시트로 가득한 사무실 생활로 변신! 하지만 반복되는 작업에 지쳐 "이걸 자동화하면 어떨까?" 생각이 들었어요. 그래서 처음에는 엑셀을 그다음에 VBA 그리고 python pandas, matplotlib numpy를 만나 행복했다가 이제는 Cursor AI를 만난 후, 제 삶이 바뀌었죠. 이제는 귀찮은 메뉴얼 작업을 자동화하고, 휴먼 에러를 잡아내는 '스마트 게으름뱅이'가 됐습니다. 비전공자지만, 필요에 따라 공부하며 여기까지 왔어요 – 데이터 분석, ETL, 자동화가 제 새로운 취미이자 무기예요!

## 💡 What I'm Obsessed With Right Now
- **ETL 파이프라인 구축**: IEC62474, EU REACH, 한국 산안법 등 글로벌 화학물질 규제 데이터를 자동으로 수집하고 표준화하는 강력한 파이프라인 개발 중! 🧪
- **통합 규제 관리**: RoHS, REACH, GADSL, Conflict Minerals 등 400개 이상의 선언 가능 물질을 단일 시스템에서 관리! 🌍
- **데이터 시각화 대시보드**: ETL로 수집한 데이터를 Streamlit으로 아름다운 대시보드로 시각화! 📊
- **업무 자동화**: 반복 작업? No thanks! Cursor AI로 뚝딱 만들어 버려요. 시간 절약 + 에러 제로 = 행복 ↑
- **데이터 마법**: 외부 데이터 스크래핑해서 ETL로 정리, 대시보드에 뿌려 분석! (회사 비밀 자료는 절대 안 써요, 오직 일반 자료만 🛡️)
- **품질 업그레이드**: 속도 향상과 실수 줄이기 – 제 업무를 '카이젠'하는 데 집중 중이에요.
- **Philosophy**: "게으르게 일하되, 똑똑하게!" 반복은 로봇에게 맡기고, 창의적인 일에 에너지를 쏟아요. 😉

## 🛠️ Tech Stack & Tools
### Core Development
- **Language**: Python (주력)
- **AI Assistant**: Cursor AI (개발 도구)
- **Version Control**: Git & GitHub

### Data Processing & Analysis
- **Data Manipulation**: Pandas, NumPy
- **Web Scraping**: BeautifulSoup, Selenium, Requests
- **Data Visualization**: Matplotlib, Seaborn, Plotly
- **Database**: SQLite, PostgreSQL (필요시)

### Automation & ETL
- **Task Automation**: Python Scripts, Batch Processing
- **Data Pipeline**: Custom ETL Scripts (EU REACH, KOSHA)
- **Web Scraping**: Selenium, BeautifulSoup, Requests
- **Data Formats**: XML, JSON, Excel (openpyxl, xlrd)
- **Scheduling**: Windows Task Scheduler, Cron (필요시)

### Data Visualization & Dashboard
- **Web Framework**: Streamlit (대시보드)
- **Interactive Charts**: Plotly, Plotly Express
- **Data Tables**: Streamlit DataFrames
- **Export Features**: CSV, Excel 다운로드

### Development Environment
- **IDE**: Cursor AI
- **OS**: Windows
- **Package Management**: pip, conda (필요시)

### Learning & Growth
- **Approach**: 필요에 따른 기술 학습
- **Focus**: 실무 적용 가능한 기술 우선
- **Method**: Cursor AI를 활용한 효율적 학습

## 📁 Project Structure
```
workflow-kaizen/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── TRANSFER_INSTRUCTIONS.txt
├── win_workflow_kaizen_transfer.zip
├── docs/
│   ├── installation.md
│   ├── transfer-installation.md
│   ├── usage.md
│   └── windows_installation.md
├── modules/
│   ├── etl-pipeline/
│   │   ├── ETL_Modules_Documentation.md
│   │   ├── iec62474_etl.py       # IEC62474 물질 선언 표준 ETL 모듈 ⭐ NEW
│   │   ├── reach_etl.py          # EU REACH 데이터 ETL 모듈
│   │   └── kosha_etl.py          # 한국 KOSHA 데이터 ETL 모듈
│   └── visualization/
│       ├── __init__.py
│       └── dashboard.py           # Streamlit ETL 데이터 대시보드
├── data/
│   ├── iec62474_substances.json  # IEC62474 수집 데이터 (RoHS, REACH, GADSL 등 통합) ⭐ NEW
│   ├── reach_data.json           # EU REACH 수집 데이터
│   ├── kosha_special_materials.json  # KOSHA 수집 데이터 (생성 시)
│   ├── json/                     # 기타 JSON 파일
│   ├── downloads/
│   ├── sqlite/
│   ├── authorisation-list-export.xml
│   ├── candidate-list-of-svhc-for-authorisation-export.xml
│   └── restriction-list-export.xml
├── config/
│   └── windows_setup.py
├── scripts/
│   └── prepare_transfer.py
├── logs/
├── kaizen-venv/                  # Python 가상환경 (개발용)
└── tests/
    ├── test_modules/
    └── test_projects/
```

## 🚀 Featured ETL Modules

### ⭐ IEC62474 통합 물질 선언 ETL 파이프라인 (NEW!)
**파일**: `modules/etl-pipeline/iec62474_etl.py`
- **목적**: 국제 표준 IEC62474 물질 선언 데이터베이스 자동 수집
- **통합 규제**: RoHS, REACH (SVHC, Annex XIV, XVII), GADSL, Conflict Minerals, TSCA, POPs, Prop 65
- **물질 범위**: 400개 이상의 선언 가능 물질 (기존 RoHS 10개 → 400개 이상으로 확장!)
- **기술**: Selenium 웹 자동화, XML 파싱, 규제 자동 분류
- **출력**: `data/iec62474_substances.json` (항상 최신 버전 유지)

```bash
# IEC62474 최신 데이터 다운로드 및 처리 (권장)
python modules/etl-pipeline/iec62474_etl.py

# 기존 XML 파일 사용
python modules/etl-pipeline/iec62474_etl.py --skip-download
```

**📖 상세 가이드**: [`docs/iec62474-etl-user-guide.md`](docs/iec62474-etl-user-guide.md)

### EU REACH 데이터 ETL 파이프라인
**파일**: `modules/etl-pipeline/reach_etl.py`
- **목적**: EU 화학물질 규제 데이터 자동 수집
- **대상 데이터**: SVHC, Annex XIV, Annex XVII 목록
- **기술**: Selenium 웹 자동화, XML 파싱
- **출력**: `data/json/reach_data.json`

```bash
# EU REACH 데이터 수집
python modules/etl-pipeline/reach_etl.py

# 기존 데이터로 테스트
python modules/etl-pipeline/reach_etl.py --skip-download
```

### 한국 KOSHA 산안법 ETL 파이프라인
**파일**: `modules/etl-pipeline/kosha_etl.py`
- **목적**: 한국 산업안전보건법 특수관리물질 데이터 수집
- **대상 데이터**: 특수관리물질, 유해화학물질 목록
- **기술**: 다중 데이터 소스 (API, 웹스크래핑, 샘플 데이터)
- **출력**: `data/json/kosha_special_materials.json`

```bash
# 한국 특수관리물질 데이터 수집 (샘플 데이터)
python modules/etl-pipeline/kosha_etl.py --data-type special_materials --skip-download

# 다른 데이터 타입 선택
python modules/etl-pipeline/kosha_etl.py --data-type hazardous_materials
```

**📖 상세 문서**: [`modules/etl-pipeline/ETL_Modules_Documentation.md`](modules/etl-pipeline/ETL_Modules_Documentation.md)

## 🔧 Technical Features
### Code Quality & Management
- **Modular Design**: 기능별 독립적인 모듈 구조
- **Reusability**: 공통 기능의 패키지화 및 재사용
- **Documentation**: 각 모듈별 상세한 README 및 주석
- **Version Control**: Git을 활용한 체계적인 버전 관리

### Portability & Compatibility
- **Cross-Environment**: 개인 PC → 회사 PC 이식성 고려 (Windows 기반)
- **Dependency Management**: requirements.txt를 통한 의존성 관리
- **Configuration**: 환경별 설정 파일 분리
- **Error Handling**: 다양한 환경에서의 안정성 확보

### Maintainability & Scalability
- **Clean Code**: 가독성 높은 코드 작성
- **Error Logging**: 상세한 로그 및 에러 추적
- **Configuration**: 설정 파일을 통한 유연한 관리
- **Testing**: 단위 테스트 및 통합 테스트

### AI-Assisted Development
- **Cursor AI Integration**: AI를 활용한 효율적인 개발
- **Rapid Prototyping**: 빠른 프로토타입 개발
- **Code Optimization**: AI 기반 코드 최적화
- **Learning Acceleration**: 새로운 기술의 빠른 습득

## ⚙️ Setup & Installation

For detailed instructions, see [docs/installation.md](docs/installation.md).

### Quick Start
```bash
# 1. 레포지토리 클론
git clone https://github.com/elcsong/workflow_kaizen.git
cd workflow-kaizen

# 2. 가상환경 생성 (권장)
python -m venv kaizen-venv
source kaizen-venv/bin/activate  # Linux/Mac
# 또는 kaizen-venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. ETL 모듈 테스트 실행
python modules/etl-pipeline/reach_etl.py --skip-download
python modules/etl-pipeline/kosha_etl.py --data-type special_materials --skip-download
```

### ETL 모듈 실행 예시
```bash
# EU REACH 데이터 수집 (실제 웹사이트에서)
python modules/etl-pipeline/reach_etl.py

# 한국 특수관리물질 데이터 수집 (샘플 데이터)
python modules/etl-pipeline/kosha_etl.py --data-type special_materials --skip-download

# 결과 확인
cat data/reach_data.json | head -20
cat data/kosha_special_materials.json | head -20
```

### 대시보드 실행
```bash
# ETL 데이터 대시보드 실행 (브라우저에서 http://localhost:8501)
streamlit run modules/visualization/dashboard.py

# 특정 포트에서 실행
streamlit run modules/visualization/dashboard.py --server.port 8502
```

Note: This project is designed for easy transfer to another Windows PC (e.g., company computer). Use virtual environments to avoid system-wide conflicts.

## 🗺️ Roadmap
### ✅ Completed
- [x] Project initial structure setup
- [x] README and documentation
- [x] ⭐ **IEC62474 통합 물질 선언 ETL 파이프라인 구축** (RoHS, REACH, GADSL 등 통합)
- [x] EU REACH 화학물질 데이터 ETL 파이프라인 구축
- [x] 한국 KOSHA 산안법 특수관리물질 ETL 파이프라인 구축
- [x] ETL 모듈 상세 문서화
- [x] Streamlit 대시보드 개발 (ETL 데이터 시각화)
- [x] 기존 RoHS ETL을 IEC62474 ETL로 통합 및 대체

### 🚧 In Progress
- [ ] IEC62474 데이터 기반 대시보드 업데이트
- [ ] Develop data-scraping module (웹 스크래핑 고도화)

### 📝 Planned
- [ ] Create visualization dashboards
- [ ] Expand automation tools
- [ ] Add more example projects
- [ ] API 기반 데이터 수집 모듈 개발

### 🔮 향후 개선 아이템 (법령정보 시스템 복구 후)
#### PDF 문서 기반 데이터 추출 모듈
**배경**: 현재 법령정보시스템 화재로 인한 접근 불가 (2025년 현재)
- **대상 문서 1**: 작업환경측정 대상 유해인자 (산업안전보건법 제186조제1항 관련)
- **대상 문서 2**: 산업안전보건기준에 관한 규칙 [별표 12] 관리대상 유해물질의 종류

**구현 계획**:
- PDF 다운로드 자동화 모듈 개발
- PDF 표 데이터 추출 및 구조화
- 물질명, CAS번호, 특별관리물질 여부 구분 로직
- JSON 데이터베이스 형태로 저장
- 기존 ETL 파이프라인과 통합

## 📫 Contact
- GitHub: [@elcsong](https://github.com/elcsong)
- Email: haemyeome@icloud.com
- LinkedIn: (Optional - add if desired)

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

