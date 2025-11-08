#!/usr/bin/env python3
"""
CLI 인터페이스 - 메인 실행 스크립트
불량 유형 판별을 위한 명령행 도구
"""
import argparse
import sys
import logging
from pathlib import Path
import pandas as pd
 
# 패키지 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
 
from intent_matcher.core.matcher import DefectMatcher
 
def setup_logging(verbose: bool = False):
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
 
def parse_arguments():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='의료 장비 불량 유형 판별 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 사용 (SBERT 없이)
  python match.py --target targets/DF_FREEZE_001.yaml --file data/complaints.xlsx
 
  # SBERT 사용
  python match.py --target targets/DF_FREEZE_001.yaml --file data/complaints.xlsx --use-sbert
 
  # 컬럼명 지정
  python match.py --target targets/DF_FREEZE_001.yaml --file data/complaints.xlsx \\
    --cols CustomerDescription,FieldEngineerNotes,RepairActions,TestResults
 
  # 가중치 조정
  python match.py --target targets/DF_FREEZE_001.yaml --file data/complaints.xlsx \\
    --alpha 0.7 --out results.csv
        """
    )
   
    # 필수 인자
    parser.add_argument(
        '--target', '-t',
        required=True,
        help='타겟 불량 정의 YAML 파일 경로'
    )
   
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='분석할 Excel 파일 경로'
    )
   
    # 선택 인자
    parser.add_argument(
        '--sheet', '-s',
        default='Sheet1',
        help='Excel 시트명 (기본값: Sheet1)'
    )
   
    parser.add_argument(
        '--cols', '-c',
        help='텍스트 컬럼명들 (콤마로 구분, 순서: Customers,FE,Actions,Test)'
    )
   
    parser.add_argument(
        '--id-col',
        help='ID 컬럼명 (선택사항)'
    )
   
    parser.add_argument(
        '--out', '-o',
        help='결과 저장 CSV 파일 경로 (기본값: 자동 생성)'
    )
   
    parser.add_argument(
        '--use-sbert',
        action='store_true',
        help='SBERT 의미 분석 사용'
    )
   
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.5,
        help='룰 vs 의미 점수 가중치 (0~1, 기본값: 0.5)'
    )
   
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세 로그 출력'
    )
   
    return parser.parse_args()
 
def validate_arguments(args):
    """인자 유효성 검증"""
    issues = []
   
    # 파일 존재 확인
    if not Path(args.target).exists():
        issues.append(f"Target file not found: {args.target}")
   
    if not Path(args.file).exists():
        issues.append(f"Input file not found: {args.file}")
   
    # alpha 범위 확인
    if not 0.0 <= args.alpha <= 1.0:
        issues.append(f"Alpha must be between 0.0 and 1.0, got {args.alpha}")
   
    return issues
 
def parse_columns(cols_str: str) -> list:
    """컬럼명 문자열 파싱"""
    if not cols_str:
        return None
   
    return [col.strip() for col in cols_str.split(',')]
 
def generate_output_filename(input_file: str, target_file: str, use_sbert: bool) -> str:
    """출력 파일명 자동 생성"""
    input_path = Path(input_file)
    target_path = Path(target_file)
   
    # 타겟 ID 추출
    target_id = target_path.stem
   
    # SBERT 사용 여부 표시
    sbert_suffix = "_sbert" if use_sbert else ""
   
    # 출력 파일명 생성
    output_name = f"results_{target_id}{sbert_suffix}.csv"
   
    return output_name
 
def main():
    """메인 실행 함수"""
    args = parse_arguments()
   
    # 로깅 설정
    setup_logging(args.verbose)
   
    # 인자 검증
    issues = validate_arguments(args)
    if issues:
        print("오류:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1
   
    try:
        # DefectMatcher 초기화
        print(f"타겟 설정 로드 중: {args.target}")
        matcher = DefectMatcher(
            target_config_path=args.target,
            use_sbert=args.use_sbert,
            alpha=args.alpha
        )
       
        # 설정 검증
        setup_issues = matcher.validate_setup()
        if setup_issues:
            print("설정 경고:", file=sys.stderr)
            for issue in setup_issues:
                print(f"  - {issue}", file=sys.stderr)
       
        # 설정 요약 출력
        config_summary = matcher.get_config_summary()
        print(f"\n=== 분석 설정 ===")
        print(f"타겟: {config_summary['target_name']} ({config_summary['target_id']})")
        print(f"증상 키워드: {config_summary['symptoms_count']}개")
        print(f"조치 힌트: {config_summary['action_hints_count']}개")
        print(f"SBERT 사용: {config_summary['use_sbert']}")
        print(f"룰/의미 가중치: {args.alpha:.1f}/{1-args.alpha:.1f}")
       
        # 텍스트 컬럼 파싱
        text_columns = parse_columns(args.cols)
       
        # Excel 파일 분석
        print(f"\nExcel 파일 분석 중: {args.file}")
        result_df = matcher.analyze_excel(
            file_path=args.file,
            sheet_name=args.sheet,
            text_columns=text_columns,
            id_column=args.id_col
        )
       
        # 결과 요약
        total_records = len(result_df)
        true_count = (result_df['SameDefect'] == 'True').sum()
        false_count = (result_df['SameDefect'] == 'False').sum()
        review_count = (result_df['SameDefect'] == 'Review').sum()
        avg_score = result_df['FinalScore'].mean()
       
        print(f"\n=== 분석 결과 요약 ===")
        print(f"총 레코드: {total_records}개")
        print(f"매칭 (True): {true_count}개 ({true_count/total_records*100:.1f}%)")
        print(f"비매칭 (False): {false_count}개 ({false_count/total_records*100:.1f}%)")
        print(f"검토 필요 (Review): {review_count}개 ({review_count/total_records*100:.1f}%)")
        print(f"평균 점수: {avg_score:.3f}")
       
        # 출력 파일 저장
        if args.out:
            output_file = args.out
        else:
            output_file = generate_output_filename(args.file, args.target, args.use_sbert)
       
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n결과 저장됨: {output_file}")
       
        # 상위 매칭 결과 미리보기
        print(f"\n=== 상위 매칭 결과 (점수순) ===")
        top_matches = result_df.nlargest(5, 'FinalScore')
        for idx, row in top_matches.iterrows():
            print(f"점수: {row['FinalScore']:.3f} | 판정: {row['SameDefect']} | "
                  f"증상: {row['SymptomEvidence'][:50]}...")
       
        return 0
       
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
 
if __name__ == '__main__':
    sys.exit(main())