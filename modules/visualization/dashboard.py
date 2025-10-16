"""
ETL 데이터 대시보드
Workflow Kaizen ETL 결과를 시각화하여 보여주는 Streamlit 대시보드

실행 방법:
    streamlit run modules/visualization/dashboard.py
"""

import streamlit as st
import pandas as pd
import json
import os
import io
from pathlib import Path
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="Workflow Kaizen - ETL 데이터 대시보드",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 경로 설정
DATA_DIR = Path(__file__).parent.parent.parent / "data"
REACH_DATA_FILE = DATA_DIR / "reach_data.json"
KOSHA_DATA_FILE = DATA_DIR / "kosha_data.json"

def load_reach_data() -> Dict[str, Any]:
    """EU REACH 데이터를 로드합니다."""
    try:
        # 파일 존재 및 크기 확인
        if not REACH_DATA_FILE.exists():
            st.error(f"REACH 데이터 파일을 찾을 수 없습니다: {REACH_DATA_FILE}")
            st.info("💡 EU REACH 데이터를 수집하려면 다음 명령을 실행하세요:")
            st.code("python modules/etl-pipeline/reach_etl.py --skip-download")
            return {}

        # 파일 크기 확인 (너무 작은 파일은 오류)
        file_size = REACH_DATA_FILE.stat().st_size
        if file_size < 10:  # 10바이트 미만은 비정상
            st.error(f"REACH 데이터 파일이 너무 작거나 손상되었습니다: {file_size} bytes")
            st.info("💡 데이터를 다시 생성하려면 다음 명령을 실행하세요:")
            st.code("python modules/etl-pipeline/reach_etl.py --skip-download")
            return {}

        with open(REACH_DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                st.error("REACH 데이터 파일이 비어있습니다.")
                return {}

            data = json.loads(content)

            # 데이터 구조 검증
            if not isinstance(data, dict):
                st.error("REACH 데이터 형식이 올바르지 않습니다 (dict 타입이 아님).")
                return {}

            # 필수 키 확인
            expected_keys = ['svhc', 'annex_xiv', 'annex_xvii']
            found_keys = [key for key in expected_keys if key in data]
            if not found_keys:
                st.error("REACH 데이터에 필요한 카테고리가 없습니다.")
                return {}

            st.success(f"✅ REACH 데이터 로드 완료: {len(found_keys)}개 카테고리")
            return data

    except json.JSONDecodeError as e:
        st.error(f"REACH 데이터 JSON 파싱 오류: {e}")
        st.info("💡 파일이 손상되었을 수 있습니다. 다음 명령으로 재생성하세요:")
        st.code("python modules/etl-pipeline/reach_etl.py --skip-download")
        return {}
    except UnicodeDecodeError as e:
        st.error(f"REACH 데이터 파일 인코딩 오류: {e}")
        st.info("💡 UTF-8 인코딩으로 파일을 다시 생성하세요.")
        return {}
    except Exception as e:
        st.error(f"REACH 데이터 로드 중 예상치 못한 오류 발생: {e}")
        return {}

def load_kosha_data() -> Dict[str, Any]:
    """한국 KOSHA 데이터를 로드합니다."""
    try:
        # 파일 존재 확인
        if not KOSHA_DATA_FILE.exists():
            st.warning("🇰🇷 KOSHA 데이터 파일이 없습니다.")
            st.info("💡 현재 한국 산안법 데이터는 샘플 데이터 기반입니다.")
            st.info("💡 법령정보시스템 복구 후 실제 데이터를 수집할 예정입니다.")
            st.code("# 향후 사용 예정\npython modules/etl-pipeline/kosha_etl.py --data-type special_materials")
            return {}

        # 파일 크기 확인
        file_size = KOSHA_DATA_FILE.stat().st_size
        if file_size < 10:  # 10바이트 미만은 비정상
            st.error(f"KOSHA 데이터 파일이 너무 작거나 손상되었습니다: {file_size} bytes")
            return {}

        with open(KOSHA_DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                st.error("KOSHA 데이터 파일이 비어있습니다.")
                return {}

            data = json.loads(content)

            # 데이터 구조 검증
            if not isinstance(data, dict):
                st.error("KOSHA 데이터 형식이 올바르지 않습니다 (dict 타입이 아님).")
                return {}

            # 메타데이터 확인
            if 'metadata' not in data:
                st.error("KOSHA 데이터에 메타데이터가 없습니다.")
                return {}

            st.success("✅ KOSHA 데이터 로드 완료 (샘플 데이터)")
            return data

    except json.JSONDecodeError as e:
        st.error(f"KOSHA 데이터 JSON 파싱 오류: {e}")
        return {}
    except UnicodeDecodeError as e:
        st.error(f"KOSHA 데이터 파일 인코딩 오류: {e}")
        return {}
    except Exception as e:
        st.error(f"KOSHA 데이터 로드 중 예상치 못한 오류 발생: {e}")
        return {}

def flatten_reach_data(reach_data: Dict[str, Any]) -> pd.DataFrame:
    """REACH 데이터를 평탄화하여 DataFrame으로 변환합니다."""
    all_data = []

    for category, category_data in reach_data.items():
        if category == "metadata":
            continue

        metadata = category_data.get("metadata", {})
        data_list = category_data.get("data", [])

        for item in data_list:
            item_copy = item.copy()
            item_copy["category"] = category
            item_copy["category_description"] = metadata.get("annex_type", category)
            all_data.append(item_copy)

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    # 컬럼명 정리
    df.columns = df.columns.str.replace('_', ' ').str.title()
    return df

def process_kosha_data(kosha_data: Dict[str, Any]) -> pd.DataFrame:
    """KOSHA 데이터를 DataFrame으로 변환합니다."""
    metadata = kosha_data.get("metadata", {})
    data_list = kosha_data.get("data", [])

    if not data_list:
        return pd.DataFrame()

    df = pd.DataFrame(data_list)
    # 컬럼명 정리 (한글 유지)
    df.columns = df.columns.str.replace('_', ' ')
    return df

def display_data_summary(df: pd.DataFrame, title: str):
    """데이터 요약 정보를 표시합니다."""
    if df.empty:
        st.warning("표시할 데이터가 없습니다.")
        return

    st.subheader(f"📊 {title} 요약")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 항목 수", len(df))

    with col2:
        # 물질명을 나타내는 컬럼 찾기
        substance_series = df.get('Substance Name') or df.get('물질명') or (df.iloc[:, 0] if len(df.columns) > 0 else None)
        unique_count = substance_series.nunique() if substance_series is not None and len(df) > 0 else 0
        st.metric("고유 물질 수", unique_count)

    with col3:
        cas_col = None
        for col in ['Cas No', 'CAS_No', 'Cas-No']:
            if col in df.columns:
                cas_col = col
                break
        if cas_col:
            valid_cas = df[cas_col].notna() & (df[cas_col] != '') & (df[cas_col] != '-')
            st.metric("CAS 번호 보유", valid_cas.sum())
        else:
            st.metric("CAS 번호 보유", "N/A")

    with col4:
        if 'Date Of Inclusion' in df.columns:
            try:
                df_copy = df.copy()
                df_copy['Date Of Inclusion'] = pd.to_datetime(df_copy['Date Of Inclusion'], errors='coerce')
                latest_date = df_copy['Date Of Inclusion'].max()
                if pd.notna(latest_date):
                    st.metric("최신 등록일", latest_date.strftime('%Y-%m-%d'))
                else:
                    st.metric("최신 등록일", "N/A")
            except:
                st.metric("최신 등록일", "N/A")
        else:
            st.metric("최신 등록일", "N/A")

def create_search_filter(df: pd.DataFrame) -> pd.DataFrame:
    """검색 및 필터링 기능을 제공합니다."""
    st.subheader("🔍 검색 및 필터링")

    col1, col2 = st.columns([2, 1])

    with col1:
        search_term = st.text_input("검색어 입력", placeholder="물질명, CAS 번호 등으로 검색")

    with col2:
        # 동적 필터링 옵션
        filter_options = ["전체"] + list(df.columns)
        selected_filter = st.selectbox("필터링할 컬럼 선택", filter_options)

    # 검색 적용
    if search_term:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        df_filtered = df[mask]
        st.info(f"검색 결과: {len(df_filtered)} 개 항목 (전체 {len(df)} 개 중)")
    else:
        df_filtered = df

    # 추가 필터링
    if selected_filter != "전체" and selected_filter in df.columns:
        unique_values = df_filtered[selected_filter].dropna().unique()
        if len(unique_values) > 0:
            selected_values = st.multiselect(
                f"{selected_filter} 필터",
                options=sorted(unique_values),
                default=[]
            )
            if selected_values:
                df_filtered = df_filtered[df_filtered[selected_filter].isin(selected_values)]

    return df_filtered

def display_data_table(df: pd.DataFrame, title: str):
    """데이터를 테이블 형태로 표시합니다."""
    st.subheader(f"📋 {title} 데이터 테이블")

    # 테이블 설정
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col: st.column_config.TextColumn(col, width="medium") for col in df.columns
        }
    )

    # 데이터 내보내기
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 CSV 다운로드"):
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV 파일 다운로드",
                data=csv_data,
                file_name=f"{title.lower().replace(' ', '_')}_data.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("📥 Excel 다운로드"):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
            buffer.seek(0)
            st.download_button(
                label="Excel 파일 다운로드",
                data=buffer,
                file_name=f"{title.lower().replace(' ', '_')}_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def create_visualizations(df: pd.DataFrame, data_type: str):
    """데이터 시각화를 생성합니다."""
    if df.empty:
        return

    st.subheader("📈 데이터 시각화")

    if data_type == "REACH":
        # REACH 데이터 시각화
        if 'Category' in df.columns:
            # 카테고리별 분포
            category_counts = df['Category'].value_counts()
            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="REACH 카테고리별 분포"
            )
            st.plotly_chart(fig, use_container_width=True)

        if 'Reason For Inclusion' in df.columns:
            # 포함 이유별 분포 (상위 10개)
            reason_counts = df['Reason For Inclusion'].value_counts().head(10)
            fig = px.bar(
                x=reason_counts.values,
                y=reason_counts.index,
                orientation='h',
                title="포함 이유별 분포 (상위 10개)"
            )
            st.plotly_chart(fig, use_container_width=True)

    elif data_type == "KOSHA":
        # KOSHA 데이터 시각화
        if '비고' in df.columns:
            # 비고별 분포
            remark_counts = df['비고'].value_counts()
            fig = px.bar(
                x=remark_counts.values,
                y=remark_counts.index,
                orientation='h',
                title="물질 특성별 분포"
            )
            st.plotly_chart(fig, use_container_width=True)

def main():
    """메인 대시보드 함수"""
    st.title("🧪 Workflow Kaizen - ETL 데이터 대시보드")
    st.markdown("---")

    # 사이드바 설정
    st.sidebar.title("🎛️ 데이터 소스 선택")

    data_source = st.sidebar.radio(
        "분석할 데이터 선택",
        ["EU REACH 데이터", "한국 KOSHA 데이터"],
        help="ETL로 수집된 화학물질 데이터를 선택하세요"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 사용 방법")
    st.sidebar.markdown("""
    1. **데이터 소스 선택**: 분석할 데이터를 선택하세요
    2. **요약 정보 확인**: 데이터의 기본 통계를 확인하세요
    3. **검색 및 필터링**: 원하는 조건으로 데이터를 필터링하세요
    4. **테이블 확인**: 상세 데이터를 테이블 형태로 확인하세요
    5. **시각화**: 데이터 분포를 차트로 확인하세요
    6. **내보내기**: 필요한 데이터를 다운로드하세요
    """)

    # 데이터 로드
    if data_source == "EU REACH 데이터":
        st.header("🇪🇺 EU REACH 화학물질 데이터")
        reach_data = load_reach_data()

        if not reach_data:
            st.error("REACH 데이터를 로드할 수 없습니다.")
            return

        # 데이터 평탄화
        df = flatten_reach_data(reach_data)

        if df.empty:
            st.warning("표시할 REACH 데이터가 없습니다.")
            return

        # 요약 정보 표시
        display_data_summary(df, "EU REACH")

        # 검색 및 필터링
        df_filtered = create_search_filter(df)

        # 데이터 테이블 표시
        display_data_table(df_filtered, "EU REACH")

        # 시각화
        create_visualizations(df_filtered, "REACH")

    else:  # 한국 KOSHA 데이터
        st.header("🇰🇷 한국 KOSHA 특수관리물질 데이터")
        kosha_data = load_kosha_data()

        if not kosha_data:
            st.error("KOSHA 데이터를 로드할 수 없습니다.")
            return

        # 데이터 처리
        df = process_kosha_data(kosha_data)

        if df.empty:
            st.warning("표시할 KOSHA 데이터가 없습니다.")
            return

        # 요약 정보 표시
        display_data_summary(df, "한국 KOSHA")

        # 검색 및 필터링
        df_filtered = create_search_filter(df)

        # 데이터 테이블 표시
        display_data_table(df_filtered, "한국 KOSHA")

        # 시각화
        create_visualizations(df_filtered, "KOSHA")

    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>🚀 Workflow Kaizen ETL 대시보드 | 데이터 출처: 공공 데이터</p>
        <p>개발자: @elcsong | <a href='https://github.com/elcsong/workflow_kaizen'>GitHub Repository</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
