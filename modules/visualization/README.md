# ETL 데이터 시각화 대시보드

Workflow Kaizen 프로젝트의 ETL 결과를 아름다운 웹 대시보드로 시각화하여 보여주는 모듈입니다.

## 📋 개요

이 대시보드는 EU REACH와 한국 KOSHA ETL 모듈에서 수집한 화학물질 데이터를 직관적으로 확인할 수 있도록 도와줍니다.

## 🚀 주요 기능

### 데이터 소스 선택
- **EU REACH 데이터**: SVHC, Annex XIV, Annex XVII 화학물질 데이터
- **한국 KOSHA 데이터**: 산업안전보건법 특수관리물질 데이터

### 데이터 분석 기능
- **요약 통계**: 총 항목 수, 고유 물질 수, CAS 번호 보유율 등
- **검색 및 필터링**: 물질명, CAS 번호 등으로 실시간 검색
- **테이블 표시**: 모든 데이터를 정렬 가능한 테이블 형태로 표시

### 시각화 기능
- **카테고리 분포**: REACH 데이터의 카테고리별 분포 (파이 차트)
- **포함 이유 분석**: SVHC 포함 이유별 통계 (막대 차트)
- **물질 특성 분포**: KOSHA 데이터의 특성별 분포

### 데이터 내보내기
- **CSV 다운로드**: 필터링된 데이터를 CSV 형식으로 내보내기
- **Excel 다운로드**: 필터링된 데이터를 Excel 형식으로 내보내기

## 🛠️ 실행 방법

### 기본 실행
```bash
# 가상환경 활성화
source kaizen-venv/bin/activate

# 대시보드 실행 (기본 포트 8501)
streamlit run modules/visualization/dashboard.py
```

### 포트 지정 실행
```bash
# 특정 포트에서 실행
streamlit run modules/visualization/dashboard.py --server.port 8502
```

### 백그라운드 실행
```bash
# 헤드리스 모드로 백그라운드 실행
streamlit run modules/visualization/dashboard.py --server.headless true --server.port 8501 &
```

## 📊 인터페이스 설명

### 사이드바 (왼쪽 패널)
- **데이터 소스 선택**: 분석할 데이터 타입 선택
- **사용 방법**: 대시보드 사용 가이드 제공

### 메인 패널 (오른쪽 영역)
1. **헤더**: 선택된 데이터 타입 표시
2. **요약 정보**: 데이터의 기본 통계 표시
3. **검색/필터링**: 실시간 검색 및 필터링 기능
4. **데이터 테이블**: 필터링된 데이터를 테이블로 표시
5. **시각화**: 데이터 분포를 차트로 시각화
6. **내보내기**: 데이터 다운로드 기능

## 📁 데이터 구조

### EU REACH 데이터
```json
{
  "svhc": {
    "metadata": {...},
    "data": [
      {
        "substance-name": "물질명",
        "cas-no": "CAS 번호",
        "reason-for-inclusion": "포함 이유",
        "date-of-inclusion": "등록일"
      }
    ]
  }
}
```

### 한국 KOSHA 데이터
```json
{
  "metadata": {...},
  "data": [
    {
      "물질명": "벤젠",
      "영문명": "Benzene",
      "CAS_No": "71-43-2",
      "관리기준": "관리 기준",
      "관리방법": "관리 방법",
      "비고": "특이사항"
    }
  ]
}
```

## 🔧 기술 스택

- **Streamlit**: 웹 대시보드 프레임워크
- **Pandas**: 데이터 처리 및 분석
- **Plotly**: 인터랙티브 차트 생성
- **Python**: 백엔드 로직

## 📈 사용 시나리오

1. **데이터 탐색**: ETL로 수집한 데이터의 전체적인 구조 파악
2. **특정 물질 검색**: CAS 번호나 물질명으로 특정 물질 찾기
3. **통계 분석**: 데이터의 분포와 패턴 분석
4. **보고서 작성**: 필터링된 데이터를 Excel로 내보내기
5. **품질 검증**: 수집된 데이터의 완전성 확인

## 🚨 주의사항

- **데이터 출처**: 모든 데이터는 공공 데이터이며, 실제 사용 시 최신 데이터로 업데이트 필요
- **샘플 데이터**: 한국 KOSHA 데이터는 현재 샘플 데이터로, 실제 운영 시 실제 데이터 소스로 교체 필요
- **브라우저 호환성**: 최신 브라우저(Chrome, Firefox, Safari, Edge)에서 최적의 성능 보장

## 🔗 관련 링크

- [ETL 모듈 문서](../etl-pipeline/ETL_Modules_Documentation.md)
- [프로젝트 메인 README](../../README.md)
- [Streamlit 공식 문서](https://docs.streamlit.io/)

## 📞 지원

문의사항이나 버그 리포트는 [GitHub Issues](../../issues)로 남겨주세요.
