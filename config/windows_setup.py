"""
Windows Environment Setup Configuration
크로스 플랫폼 호환성을 위한 Windows 환경 설정
"""

import os
import platform
from pathlib import Path

def get_platform_config():
    """현재 플랫폼에 따른 설정 반환"""
    system = platform.system()
    
    config = {
        'platform': system,
        'is_windows': system == "Windows",
        'is_mac': system == "Darwin",
        'is_linux': system == "Linux"
    }
    
    # WebDriver 설정
    if system == "Windows":
        config.update({
            'webdriver': 'edge',
            'webdriver_options': 'EdgeOptions',
            'webdriver_service': 'EdgeService',
            'default_encoding': 'cp1252',
            'path_separator': '\\'
        })
    else:
        config.update({
            'webdriver': 'chrome',
            'webdriver_options': 'ChromeOptions', 
            'webdriver_service': 'ChromeService',
            'default_encoding': 'utf-8',
            'path_separator': '/'
        })
    
    return config

def get_data_paths():
    """플랫폼별 데이터 경로 설정"""
    base_path = Path.cwd()
    
    paths = {
        'data_dir': base_path / 'data',
        'json_dir': base_path / 'data' / 'json',
        'sqlite_dir': base_path / 'data' / 'sqlite',
        'logs_dir': base_path / 'logs',
        'config_dir': base_path / 'config',
        'downloads_dir': base_path / 'data' / 'downloads'
    }
    
    # Windows에서 경로 생성
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths

def get_webdriver_config():
    """WebDriver 설정"""
    config = get_platform_config()
    
    webdriver_config = {
        'headless': True,
        'disable_gpu': True,
        'no_sandbox': True,
        'disable_dev_shm_usage': True,
        'disable_web_security': True,
        'allow_running_insecure_content': True,
        'window_size': '1920,1080'
    }
    
    # Windows 특화 설정
    if config['is_windows']:
        webdriver_config.update({
            'edge_binary_location': None,  # 시스템 기본 Edge 사용
            'edge_driver_path': None,      # PATH에서 자동 탐지
        })
    else:
        webdriver_config.update({
            'chrome_binary_location': None,  # 시스템 기본 Chrome 사용
            'chrome_driver_path': None,      # PATH에서 자동 탐지
        })
    
    return webdriver_config

def get_encoding_config():
    """인코딩 설정"""
    config = get_platform_config()
    
    # CSV 파일 읽기용 인코딩 우선순위
    if config['is_windows']:
        encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
    else:
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    return {
        'csv_encodings': encodings,
        'default_encoding': config['default_encoding'],
        'json_encoding': 'utf-8'
    }

def get_logging_config():
    """로깅 설정"""
    paths = get_data_paths()
    
    return {
        'log_level': 'INFO',
        'log_file': paths['logs_dir'] / 'workflow_kaizen.log',
        'max_log_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }

def validate_environment():
    """환경 검증"""
    config = get_platform_config()
    issues = []
    
    # Python 버전 확인
    python_version = platform.python_version()
    major, minor = map(int, python_version.split('.')[:2])
    if major < 3 or (major == 3 and minor < 8):
        issues.append(f"Python 3.8+ 권장, 현재: {python_version}")
    
    # 필수 디렉토리 확인
    paths = get_data_paths()
    for name, path in paths.items():
        if not path.exists():
            issues.append(f"필수 디렉토리 없음: {name} ({path})")
    
    # WebDriver 확인 (선택사항)
    try:
        if config['is_windows']:
            from selenium.webdriver.edge.options import Options
        else:
            from selenium.webdriver.chrome.options import Options
    except ImportError as e:
        issues.append(f"WebDriver 옵션 import 실패: {e}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'config': config
    }

if __name__ == "__main__":
    # 환경 검증 실행
    validation = validate_environment()
    
    print("=== Windows 호환성 환경 검증 ===")
    print(f"플랫폼: {validation['config']['platform']}")
    print(f"검증 결과: {'✅ 통과' if validation['valid'] else '❌ 실패'}")
    
    if validation['issues']:
        print("\n발견된 문제점:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    else:
        print("\n모든 검증 통과! Windows 환경에서 실행 준비 완료.")
    
    print(f"\n데이터 경로:")
    paths = get_data_paths()
    for name, path in paths.items():
        print(f"  {name}: {path}")
