# 메일 전송을 통한 설치 가이드 (GitHub 사용 불가 시)

이 가이드는 보안 정책으로 GitHub를 사용할 수 없을 때, 로컬 폴더를 메일로 전송하고 회사 PC에 설치하는 방법을 설명합니다. 기존 [installation.md](installation.md)를 보완하며, 충돌 방지와 이식성을 중점으로 합니다.

## 1. 준비: 개인 PC에서 폴더 압축
- **압축 방법**: C:\workflow-kaizen 폴더를 ZIP으로 압축하세요.
  - Windows 탐색기: 폴더 우클릭 > 보내기 > 압축(ZIP) 폴더.
  - PowerShell 명령어:
    ```
    Compress-Archive -Path C:\workflow-kaizen\* -DestinationPath C:\workflow-kaizen.zip
    ```
- **포함 파일 확인**: README.md, LICENSE, .gitignore, docs/ 등 모든 파일 포함. 불필요한 파일(임시 파일)은 삭제 후 압축.
- **크기 관리**: ZIP 파일이 25MB 초과 시 Google Drive나 OneDrive로 공유 (메일 첨부 제한 고려).

## 2. 메일 전송
- ZIP 파일을 회사 메일로 첨부/공유하세요. (보안: 민감 데이터 없음 확인 – 회사 자료 절대 포함 금지.)
- 대안: USB나 클라우드 스토리지 사용 (회사 정책 준수).

## 3. 회사 PC에서의 설치
### 3.1 압축 해제
- ZIP 파일 다운로드 후 우클릭 > 모두 추출 (대상 폴더: C:\workflow-kaizen 추천).
- 결과: 원본 폴더 구조 복원 (modules/, projects/, docs/ 등).

### 3.2 Python 확인 및 설치
- Python 3.8+ 설치 확인: 터미널에서 `python --version`.
- 없으면 [python.org](https://www.python.org/)에서 다운로드/설치. (회사 보안으로 다운로드 제한 시 IT 부서 문의.)

### 3.3 가상환경 생성 (충돌 방지)
- 기존 venv 충돌 피하기 위해 새 이름 'kaizen-venv' 사용 (사용자 지정 가능).
- 명령어:
  ```
  cd C:\workflow-kaizen
  python -m venv kaizen-venv
  .\kaizen-venv\Scripts\activate
  ```
- 활성화 확인: 프롬프트에 (kaizen-venv) 표시.
- 대안: Conda 사용 시 `conda create -n kaizen-venv python=3.8` 후 `conda activate kaizen-venv`.

### 3.4 Dependencies 설치
- requirements.txt가 있으면:
  ```
  pip install -r requirements.txt
  ```
- 없으면 필요한 패키지 설치 (예: `pip install pandas numpy requests beautifulsoup4`) 후 `pip freeze > requirements.txt`로 생성.
- 환경 변수: `.env.example`을 `.env`로 복사 후 값 채우기 (예: DB_URL).

### 3.5 테스트 및 실행
- 간단 테스트:
  ```
  python -c "import pandas; print('Setup successful!')"
  ```
- 프로젝트 실행: [usage.md](usage.md) 참조 (예: projects/project-1/main.py 실행).
- Git 로컬 설정 (선택): Git 설치 후 `git init`으로 버전 관리 (원격 푸시 불가 시 로컬만 사용).

## 4. 문제 해결 (Troubleshooting)
- **충돌 발생**: 가상환경 사용으로 시스템 패키지 영향 최소화. 기존 venv 비활성화/삭제.
- **권한 에러**: 관리자 권한으로 터미널 실행.
- **Python 버전 불일치**: 회사 PC 버전 확인 후 맞춤 (docs/installation.md 참조).
- **보안 제한**: 설치 불가 시 IT 지원 요청. 상대 경로 사용으로 경로 문제 피함.
- 추가 도움: README.md의 Contact 섹션 참조 또는 메일로 문의.

이 가이드를 통해 회사 PC에서 쉽게 설치하세요. 피드백 환영!
