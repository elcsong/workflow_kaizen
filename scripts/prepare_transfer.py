#!/usr/bin/env python3
"""
프로젝트 전송 준비 스크립트
회사 PC로 전송하기 전에 불필요한 파일들을 정리하고 압축을 준비합니다.
"""

import os
import shutil
import zipfile
from pathlib import Path
import argparse

def clean_project_directory(project_dir: Path):
    """프로젝트 디렉토리에서 불필요한 파일들 제거"""
    print("🧹 프로젝트 정리 중...")
    
    # 제거할 파일/폴더 패턴
    patterns_to_remove = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        '.coverage',
        'htmlcov',
        '.mypy_cache',
        '.DS_Store',
        'Thumbs.db',
        '*.log',
        'venv',
        'env',
        '.env',
        'node_modules',
        '.git',
        '*.tmp',
        '*.temp'
    ]
    
    removed_count = 0
    
    for pattern in patterns_to_remove:
        if '*' in pattern:
            # 와일드카드 패턴
            for file_path in project_dir.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=True)
                    removed_count += 1
        else:
            # 정확한 이름
            for file_path in project_dir.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=True)
                    removed_count += 1
    
    print(f"✅ {removed_count}개의 불필요한 파일/폴더 제거 완료")

def create_transfer_package(project_dir: Path, output_path: Path):
    """전송용 압축 파일 생성"""
    print(f"📦 압축 파일 생성 중: {output_path}")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                # 상대 경로로 압축
                arcname = file_path.relative_to(project_dir.parent)
                zipf.write(file_path, arcname)
    
    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
    print(f"✅ 압축 완료: {file_size:.1f}MB")
    
    if file_size > 25:
        print("⚠️  파일 크기가 25MB를 초과합니다. 이메일 첨부 대신 클라우드 스토리지 사용을 권장합니다.")

def create_transfer_instructions(project_dir: Path):
    """전송 지침 파일 생성"""
    instructions_file = project_dir / "TRANSFER_INSTRUCTIONS.txt"
    
    instructions = r"""
# 프로젝트 전송 지침

## 📋 전송 방법

### 방법 1: 이메일 첨부 (25MB 이하)
1. 이 ZIP 파일을 이메일로 첨부
2. 회사 PC에서 다운로드 후 압축 해제

### 방법 2: USB 메모리
1. ZIP 파일을 USB에 복사
2. 회사 PC에서 USB 연결 후 복사

### 방법 3: 클라우드 스토리지
1. OneDrive/Google Drive에 업로드
2. 회사 PC에서 다운로드

## 🚀 회사 PC 설치 과정

1. 압축 해제
   ```
   # Windows 탐색기에서 우클릭 > 모두 추출
   # 또는 PowerShell:
   Expand-Archive -Path win_workflow_kaizen.zip -DestinationPath C:\
   ```

2. 가상환경 생성
   ```
   cd C:\win_workflow_kaizen
   python -m venv kaizen-venv
   kaizen-venv\Scripts\activate
   ```

3. 의존성 설치
   ```
   pip install -r requirements.txt
   ```

4. 환경 검증
   ```
   python config/windows_setup.py
   ```

## 📞 문제 해결

문제 발생 시:
1. `python config/windows_setup.py` 실행
2. 로그 파일 확인: `logs/workflow_kaizen.log`
3. README.md 참조

## ⚠️ 주의사항

- 회사 보안 정책 준수
- 민감한 데이터 포함 금지
- Python 3.8+ 필요
- Microsoft Edge 브라우저 필요 (Windows 10/11)
"""
    
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✅ 전송 지침 파일 생성: {instructions_file}")

def main():
    parser = argparse.ArgumentParser(description='프로젝트 전송 준비')
    parser.add_argument('--output', '-o', default='win_workflow_kaizen_transfer.zip',
                       help='출력 압축 파일명 (기본: win_workflow_kaizen_transfer.zip)')
    parser.add_argument('--clean-only', action='store_true',
                       help='정리만 수행하고 압축은 하지 않음')
    
    args = parser.parse_args()
    
    # 현재 프로젝트 디렉토리
    project_dir = Path.cwd()
    output_path = Path(args.output)
    
    print("🚀 프로젝트 전송 준비 시작")
    print(f"📁 프로젝트 디렉토리: {project_dir}")
    
    # 1. 프로젝트 정리
    clean_project_directory(project_dir)
    
    if not args.clean_only:
        # 2. 압축 파일 생성
        create_transfer_package(project_dir, output_path)
        
        # 3. 전송 지침 생성
        create_transfer_instructions(project_dir)
        
        print("\n🎉 전송 준비 완료!")
        print(f"📦 압축 파일: {output_path}")
        print("📋 전송 지침: TRANSFER_INSTRUCTIONS.txt")
        print("\n다음 단계:")
        print("1. 압축 파일을 회사 PC로 전송")
        print("2. TRANSFER_INSTRUCTIONS.txt 참조하여 설치")
    else:
        print("\n✅ 프로젝트 정리 완료!")

if __name__ == "__main__":
    main()
