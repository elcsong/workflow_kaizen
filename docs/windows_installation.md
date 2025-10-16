# Windows 환경 설치 가이드 (회사 PC용)

## 🎯 목표
Mac에서 개발한 Workflow Kaizen 프로젝트를 회사 Windows 환경에서 원활하게 실행하기 위한 설치 및 설정 가이드입니다.
**GitHub 사용이 불가능한 회사 환경**을 고려한 전송 및 설치 방법을 제공합니다.

## 📋 사전 요구사항

### 1. Python 설치
- **Python 3.9 이상** 설치 권장 (현재 개발 환경: Python 3.9)
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드
- 설치 시 **"Add Python to PATH"** 옵션 체크 필수
- 회사 보안 정책으로 다운로드 제한 시 IT 부서 문의

### 2. Microsoft Edge WebDriver
- Windows 10/11에는 Edge가 기본 설치됨
- Edge WebDriver는 자동으로 관리됨 (selenium 4.0+)

### 3. 추가 소프트웨어 (PDF 처리용)
- **Java Runtime Environment (JRE)**: tabula-py 라이브러리용
  - [Oracle JRE 다운로드](https://www.oracle.com/java/technologies/javase-jre8-downloads.html) 또는
  - [OpenJDK](https://adoptium.net/) 사용
- **OpenCV**: camelot-py 라이브러리용 (선택사항)

## 🚀 설치 과정

### 1. 프로젝트 전송 (GitHub 사용 불가 시)

#### 자동 생성된 전송 파일 사용 (권장)
프로젝트 루트에 이미 준비된 파일들을 사용하세요:

- **`win_workflow_kaizen_transfer.zip`**: 전송용 압축 파일 (개발용 파일 제외)
- **`TRANSFER_INSTRUCTIONS.txt`**: 설치 지침 파일

**전송 방법:**
1. 위 두 파일을 이메일 첨부 또는 USB로 전송
2. 회사 PC에서 압축 해제 후 설치 진행

#### 수동 압축 생성 (필요시)
```bash
# Mac에서 압축 생성 (.gitignore 파일 제외)
cd /Users/chikang/projects
zip -r win_workflow_kaizen.zip win_workflow_kaizen/ \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*kaizen-venv*"
```

**전송 방법:**
- 이메일 첨부 (25MB 이하 권장)
- USB 메모리
- 클라우드 스토리지 (회사 정책 준수)
- OneDrive/Google Drive 공유

### 2. 회사 PC에서 압축 해제/복사
```bash
# 압축 해제 (ZIP 파일인 경우)
# Windows 탐색기: 우클릭 > 모두 추출
# 또는 PowerShell:
Expand-Archive -Path win_workflow_kaizen.zip -DestinationPath C:\

# 결과: C:\win_workflow_kaizen\ 폴더 생성
cd C:\win_workflow_kaizen
```

### 3. 가상환경 생성 (충돌 방지)
```bash
# 기존 venv 충돌 피하기 위해 새 이름 사용
python -m venv kaizen-venv

# 가상환경 활성화 (Command Prompt)
kaizen-venv\Scripts\activate

# 가상환경 활성화 (PowerShell)
kaizen-venv\Scripts\Activate.ps1

# 활성화 확인: 프롬프트에 (kaizen-venv) 표시
```

### 4. 의존성 설치
```bash
# 기본 요구사항 설치
pip install -r requirements.txt

# 또는 개별 설치 (선택사항)
pip install pandas numpy requests beautifulsoup4 selenium matplotlib seaborn plotly fastapi uvicorn streamlit python-dotenv schedule

# PDF 처리 라이브러리 (법령정보시스템 PDF 파싱용)
pip install pdfplumber tabula-py PyPDF2 camelot-py[cv]

# 개발/테스트용 라이브러리 (선택사항 - 업무 환경에서는 불필요)
pip install pytest black flake8
```

**라이브러리별 설치 권장사항:**
- **필수**: pandas, numpy, requests, selenium, streamlit
- **권장**: matplotlib, plotly (시각화용)
- **선택**: PDF 라이브러리들 (법령정보시스템 복구 후 사용)
- **개발용**: pytest, black, flake8 (개발 환경에서만)

### 5. 환경 검증
```bash
python config/windows_setup.py
```

## 🔧 Windows 특화 설정

### 1. 경로 설정
- 모든 경로는 `pathlib.Path` 사용으로 자동 처리
- Windows 경로 구분자(`\`) 자동 변환

### 2. 인코딩 설정
- CSV 파일: `cp1252` (Windows 기본) 우선, `utf-8` 폴백
- JSON 파일: `utf-8` 고정
- 자동 인코딩 감지 및 변환

### 3. WebDriver 설정
- **Windows**: Microsoft Edge 사용
- **개발환경(Mac)**: Chrome 사용
- 자동 브라우저 감지 및 설정

## 📁 프로젝트 구조 (현재 버전)
```
workflow_kaizen/
├── README.md                    # 프로젝트 메인 문서
├── requirements.txt             # Python 의존성 목록
├── LICENSE                      # MIT 라이선스
├── TRANSFER_INSTRUCTIONS.txt    # 전송 설치 지침
├── win_workflow_kaizen_transfer.zip  # 전송용 압축 파일
├── docs/                        # 문서 폴더
│   ├── installation.md          # 일반 설치 가이드
│   ├── transfer-installation.md # 전송 설치 가이드
│   ├── usage.md                 # 사용법
│   └── windows_installation.md  # Windows 설치 가이드 (현재 파일)
├── config/                      # 설정 파일
│   └── windows_setup.py         # Windows 환경 검증 스크립트
├── modules/                     # 기능 모듈들
│   ├── etl-pipeline/           # ETL 파이프라인 모듈
│   │   ├── ETL_Modules_Documentation.md
│   │   ├── reach_etl.py        # EU REACH 데이터 ETL
│   │   └── kosha_etl.py        # 한국 KOSHA 데이터 ETL
│   ├── pdf-parser/             # PDF 파서 모듈 (향후 사용)
│   │   ├── __init__.py
│   │   ├── pdf_parser.py       # PDF 화학물질 추출
│   │   └── README.md           # PDF 파서 문서
│   └── visualization/          # 시각화 모듈
│       ├── __init__.py
│       ├── dashboard.py        # Streamlit 대시보드
│       └── README.md           # 대시보드 문서
├── data/                        # 데이터 저장소
│   ├── json/                   # JSON 데이터 파일들
│   │   ├── reach_data.json     # EU REACH 수집 데이터
│   │   └── kosha_data.json     # KOSHA 수집 데이터 (실행 후 생성)
│   ├── downloads/              # 웹 스크래핑 다운로드 파일들
│   ├── sqlite/                 # SQLite 데이터베이스
│   ├── *.xml                   # ECHA XML 파일들
│   └── pdfs/                   # PDF 파일 저장소 (향후 사용)
├── scripts/                     # 유틸리티 스크립트
│   └── prepare_transfer.py     # 전송 준비 스크립트
├── logs/                        # 로그 파일들
└── kaizen-venv/                 # Python 가상환경 (생성 후)
                                   # (.gitignore에 의해 Git에서 제외)
```

## 🧪 테스트 실행

### 1. 환경 검증
```bash
python config/windows_setup.py
```

### 2. ETL 모듈 테스트

#### EU REACH 데이터 ETL
```bash
# 저장된 데이터로 테스트
python modules/etl-pipeline/reach_etl.py --skip-download

# 실제 웹에서 데이터 수집 (시간 오래 걸림)
python modules/etl-pipeline/reach_etl.py
```

#### 한국 KOSHA 데이터 ETL
```bash
# 실제 데이터 수집 시도 (현재 실패할 수 있음)
python modules/etl-pipeline/kosha_etl.py --data-type special_materials
```

### 3. 대시보드 테스트
```bash
# ETL 데이터 시각화 대시보드 실행
streamlit run modules/visualization/dashboard.py

# 브라우저에서 http://localhost:8501 접속
```

### 4. PDF 파서 테스트 (법령정보시스템 복구 후)
```bash
# PDF 파일에서 데이터 추출 테스트
python modules/pdf-parser/pdf_parser.py --url "https://example.com/document.pdf" --output "test_output.json"
```

### 5. 전체 프로젝트 테스트 (개발용)
```bash
# pytest가 설치된 경우에만
python -m pytest tests/
```

## ⚠️ 문제 해결

### 1. WebDriver 오류
```
WebDriver initialization failed
```
**해결방법:**
- Edge 브라우저가 설치되어 있는지 확인
- Windows 업데이트 실행
- `pip install --upgrade selenium webdriver-manager` 실행
- Edge 버전이 최신인지 확인

### 2. PDF 라이브러리 설치 오류

#### Java 관련 오류 (tabula-py)
```
Java not found
```
**해결방법:**
- Java JRE 설치: https://adoptium.net/
- 환경변수 `JAVA_HOME` 설정
- 시스템 PATH에 Java 경로 추가

#### OpenCV 관련 오류 (camelot-py)
```
OpenCV not found
```
**해결방법:**
- `pip install opencv-python` 실행
- 또는 camelot-py 제외하고 다른 PDF 라이브러리 사용

### 3. 인코딩 오류
```
UnicodeDecodeError: 'charmap' codec can't decode
```
**해결방법:**
- 자동 인코딩 감지 기능 사용
- CSV 파일을 UTF-8로 저장 후 재시도
- 명령 프롬프트에서 `chcp 65001` 실행 (UTF-8 모드)

### 4. 권한 오류
```
PermissionError: [Errno 13] Permission denied
```
**해결방법:**
- 관리자 권한으로 Command Prompt 실행
- 회사 PC 보안 정책 확인
- 파일 쓰기 권한이 있는 폴더에 프로젝트 설치

### 5. 메모리 부족 오류
```
MemoryError
```
**해결방법:**
- 대용량 데이터 처리 시 메모리 모니터링
- `--skip-download` 옵션으로 기존 데이터 사용
- 데이터 청크 단위 처리 고려

## 🔄 Mac → Windows 이전 체크리스트

### 개발 환경 (Mac) - 현재 프로젝트 준비 상태
- [x] **EU REACH ETL 모듈** 개발 완료
- [x] **한국 KOSHA ETL 모듈** 개발 완료 (샘플 데이터 기반)
- [x] **Streamlit 대시보드** 개발 완료
- [x] **PDF 파서 모듈** 기초 구조 구현 (법령정보시스템 복구 대기)
- [x] **GitHub 연동** 완료
- [x] **win_workflow_kaizen_transfer.zip** 파일 준비됨
- [x] **TRANSFER_INSTRUCTIONS.txt** 설치 지침 준비됨
- [ ] 프로젝트 폴더 압축 전송 (선택사항)

### 전송 방법 선택 (GitHub 사용 불가 환경용)
- [x] **방법 A**: win_workflow_kaizen_transfer.zip 파일 사용 (권장)
- [ ] **방법 B**: ZIP 압축 → 이메일/USB/클라우드 전송
- [ ] **방법 C**: USB 메모리 직접 복사
- [ ] **방법 D**: 클라우드 스토리지 공유 (회사 정책 확인)

### 회사 PC 환경 설치
- [ ] Python 3.9+ 설치 확인
- [ ] win_workflow_kaizen_transfer.zip 파일 압축 해제
- [ ] `C:\win_workflow_kaizen` 경로에 프로젝트 복사
- [ ] 가상환경 생성 (`python -m venv kaizen-venv`)
- [ ] 가상환경 활성화 (`kaizen-venv\Scripts\activate`)
- [ ] 의존성 설치 (`pip install -r requirements.txt`)
- [ ] PDF 라이브러리 설치 (선택사항)
- [ ] 환경 검증 (`python config/windows_setup.py`)
- [ ] ETL 모듈 테스트 (`python modules/etl-pipeline/reach_etl.py --skip-download`)
- [ ] 대시보드 테스트 (`streamlit run modules/visualization/dashboard.py`)

## 📞 지원

문제가 발생하면:

### 1. 기본 문제 해결
1. `python config/windows_setup.py` 실행하여 환경 검증
2. 로그 파일 확인: `logs/workflow_kaizen.log`
3. `pip list`로 설치된 패키지 확인

### 2. 모듈별 문제 해결

#### ETL 모듈 관련
- **REACH 데이터 문제**: `python modules/etl-pipeline/reach_etl.py --skip-download` 테스트
- **KOSHA 데이터 문제**: 현재 샘플 데이터 기반으로 동작 (실제 데이터 추출 실패 시)
- **인코딩 오류**: 명령 프롬프트에서 `chcp 65001` 실행 후 재시도

#### 대시보드 관련
- **Streamlit 실행 실패**: `pip install --upgrade streamlit` 실행
- **포트 충돌**: `streamlit run modules/visualization/dashboard.py --server.port 8502`

#### PDF 라이브러리 관련
- **Java 오류**: OpenJDK 설치 후 JAVA_HOME 환경변수 설정
- **OpenCV 오류**: `pip install opencv-python` 실행

### 3. 추가 지원
- **TRANSFER_INSTRUCTIONS.txt** 파일 참조
- **docs/installation.md** 일반 설치 가이드 확인
- **docs/usage.md** 사용법 가이드 확인
- 회사 IT 부서에 Python 환경 설치 문의

## 🎉 완료!

Windows 환경에서 프로젝트가 정상적으로 실행되면, 다음과 같은 메시지가 표시됩니다:

### 환경 검증 성공
```
=== Windows 호환성 환경 검증 ===
플랫폼: Windows
Python 버전: 3.9.x
필수 패키지: 모두 설치됨
WebDriver: Microsoft Edge 준비됨

검증 결과: ✅ 통과
모든 검증 통과! Windows 환경에서 실행 준비 완료.
```

### 사용 가능한 기능들
설치 완료 후 다음과 같은 기능들을 사용할 수 있습니다:

1. **EU REACH 데이터 분석**
   ```bash
   python modules/etl-pipeline/reach_etl.py --skip-download
   ```

2. **대시보드 실행**
   ```bash
   streamlit run modules/visualization/dashboard.py
   # 브라우저에서 http://localhost:8501 접속
   ```

3. **프로젝트 구조 확인**
   ```
   C:\win_workflow_kaizen\
   ├── data\json\reach_data.json     # EU REACH 데이터
   ├── modules\                      # 모든 모듈들
   ├── kaizen-venv\                  # 가상환경
   └── docs\                         # 문서들
   ```

**🎊 Workflow Kaizen 프로젝트 Windows 환경 설치 완료!**
