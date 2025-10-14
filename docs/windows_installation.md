# Windows 환경 설치 가이드 (회사 PC용)

## 🎯 목표
Mac에서 개발한 코드를 회사 Windows 환경에서 원활하게 실행하기 위한 설치 및 설정 가이드입니다.
**GitHub 사용이 불가능한 회사 환경**을 고려한 전송 및 설치 방법을 제공합니다.

## 📋 사전 요구사항

### 1. Python 설치
- **Python 3.8 이상** 설치 필요
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드
- 설치 시 **"Add Python to PATH"** 옵션 체크 필수
- 회사 보안 정책으로 다운로드 제한 시 IT 부서 문의

### 2. Microsoft Edge WebDriver
- Windows 10/11에는 Edge가 기본 설치됨
- Edge WebDriver는 자동으로 관리됨 (selenium 4.0+)

## 🚀 설치 과정

### 1. 프로젝트 전송 (GitHub 사용 불가 시)

#### 방법 A: 압축 파일 전송
```bash
# Mac에서 압축 생성
cd /Users/chikang/projects
zip -r win_workflow_kaizen.zip win_workflow_kaizen/
```

**전송 방법:**
- 이메일 첨부 (25MB 이하)
- USB 메모리
- 클라우드 스토리지 (회사 정책 준수)
- OneDrive/Google Drive 공유

#### 방법 B: 직접 복사
- 프로젝트 폴더 전체를 USB나 외장 하드에 복사
- 회사 PC의 `C:\workflow_kaizen` 경로에 복사

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
# requirements.txt가 있는 경우
pip install -r requirements.txt

# 없으면 수동 설치
pip install pandas numpy requests beautifulsoup4 selenium matplotlib seaborn plotly fastapi streamlit python-dotenv schedule
```

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

## 📁 디렉토리 구조
```
workflow_kaizen/
├── data/                 # 데이터 저장소
│   ├── json/            # JSON 데이터
│   ├── sqlite/          # SQLite 데이터베이스
│   └── downloads/       # 다운로드 파일
├── config/              # 설정 파일
├── modules/             # 모듈들
├── logs/                # 로그 파일
└── requirements.txt     # 의존성 목록
```

## 🧪 테스트 실행

### 1. 환경 검증
```bash
python config/windows_setup.py
```

### 2. REACH ETL 테스트
```bash
cd modules/etl-pipeline
python reach_etl.py --skip-download
```

### 3. 전체 프로젝트 테스트
```bash
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
- `pip install --upgrade selenium` 실행

### 2. 인코딩 오류
```
UnicodeDecodeError: 'charmap' codec can't decode
```
**해결방법:**
- 자동 인코딩 감지 기능 사용
- CSV 파일을 UTF-8로 저장 후 재시도

### 3. 경로 오류
```
FileNotFoundError: [Errno 2] No such file or directory
```
**해결방법:**
- `pathlib.Path` 사용으로 자동 해결
- 상대 경로 사용 권장

## 🔄 Mac → Windows 이전 체크리스트

### 개발 환경 (Mac)
- [ ] 코드 작성 및 테스트 완료
- [ ] `git add . && git commit -m "Windows 호환성 수정"`
- [ ] `git push origin main`
- [ ] 프로젝트 폴더 압축 또는 USB 복사
- [ ] 불필요한 파일 삭제 (__pycache__, .pyc 등)

### 전송 방법 선택
- [ ] **방법 A**: ZIP 압축 → 이메일/USB/클라우드 전송
- [ ] **방법 B**: USB 메모리 직접 복사
- [ ] **방법 C**: 클라우드 스토리지 공유 (회사 정책 확인)

### 회사 PC 환경
- [ ] Python 3.8+ 설치 확인
- [ ] 프로젝트 파일 압축 해제/복사
- [ ] 가상환경 생성 (`kaizen-venv`)
- [ ] 가상환경 활성화
- [ ] 의존성 설치
- [ ] 환경 검증 실행
- [ ] 테스트 실행

## 📞 지원

문제가 발생하면:
1. `python config/windows_setup.py` 실행하여 환경 검증
2. 로그 파일 확인: `logs/workflow_kaizen.log`
3. GitHub Issues에 문제 보고

## 🎉 완료!

Windows 환경에서 프로젝트가 정상적으로 실행되면, 다음과 같은 메시지가 표시됩니다:
```
=== Windows 호환성 환경 검증 ===
플랫폼: Windows
검증 결과: ✅ 통과

모든 검증 통과! Windows 환경에서 실행 준비 완료.
```
