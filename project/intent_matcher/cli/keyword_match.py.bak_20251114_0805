#!/usr/bin/env python3
"""
키워드 기반 필터링 CLI 인터페이스
사용자 제공 키워드로 엑셀 데이터 필터링 및 분석
"""
import argparse
import sys
import logging
from pathlib import Path
import pandas as pd
 
# 패키지 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
 
from intent_matcher.core.keyword_matcher import KeywordBasedMatcher
 
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
        description='키워드 기반 의료기기 불량 데이터 필터링 및 분석 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 키워드 필터링
  python keyword_match.py --file data/complaints.xlsx --keywords "blood,bleed,crystal"
 
  # 유사도 임계값 조정
  python keyword_match.py --file data/complaints.xlsx --keywords "freeze,hang" --threshold 0.8
 
  # SBERT 의미 분석 포함
  python keyword_match.py --file data/complaints.xlsx --keywords "artifact,image" --use-sbert
 
  # 결과 파일 지정
  python keyword_match.py --file data/complaints.xlsx --keywords "battery,power" --output results.xlsx
 
  # 자세한 로그 출력
  python keyword_match.py --file data/complaints.xlsx --keywords "probe,transducer" --verbose
 
키워드 매칭 규칙:
  - 대소문자 무관 매칭 (Blood, BLOOD, blood 모두 매칭)
  - 유사 단어 매칭 (bleed -> bleeding, bleedy, blooded 등)
  - 어간 변화 지원 (crystal -> crystals, freeze -> freezing 등)
  - 유사도 기반 퍼지 매칭 (임계값 이상의 유사 단어 포함)
        """
    )
   
    # 필수 인자
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='분석할 Excel 파일 경로'
    )
   
    parser.add_argument(
        '--keywords', '-k',
        required=True,
        help='필터링 키워드들 (콤마로 구분, 예: "blood,bleed,crystal")'
    )
   
    # 선택 인자
    parser.add_argument(
        '--sheet', '-s',
        default='Sheet1',
        help='Excel 시트명 (기본값: Sheet1)'
    )
   
    parser.add_argument(
        '--output', '-o',
        help='결과 저장 Excel 파일 경로 (기본값: 자동 생성)'
    )
   
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.8,
        help='유사 키워드 매칭 임계값 (0.0~1.0, 기본값: 0.8)'
    )
   
    parser.add_argument(
        '--use-sbert',
        action='store_true',
        help='SBERT 의미 분석 사용 (더 정확하지만 느림)'
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
    if not Path(args.file).exists():
        issues.append(f"Input file not found: {args.file}")
   
    # 키워드 확인
    if not args.keywords.strip():
        issues.append("Keywords cannot be empty")
   
    # 임계값 범위 확인
    if not 0.0 <= args.threshold <= 1.0:
        issues.append(f"Threshold must be between 0.0 and 1.0, got {args.threshold}")
   
    # alpha 범위 확인
    if not 0.0 <= args.alpha <= 1.0:
        issues.append(f"Alpha must be between 0.0 and 1.0, got {args.alpha}")
   
    return issues
 
def print_analysis_summary(summary: dict, result_df: pd.DataFrame):
    """분석 결과 요약 출력"""
    print(f"\n{'='*50}")
    print(f"키워드 기반 필터링 분석 결과")
    print(f"{'='*50}")
   
    print(f"총 레코드 수: {summary['total_records']:,}개")
    print(f"필터링된 레코드 수: {summary['filtered_records']:,}개")
    print(f"필터링 비율: {summary['filter_rate']:.1f}%")
    print(f"사용된 키워드: {', '.join(summary['keywords_used'])}")
   
    if len(result_df) > 0:
        print(f"\n{'='*30}")
        print(f"상위 매칭 결과 미리보기")
        print(f"{'='*30}")
       
        for i, (idx, row) in enumerate(result_df.head().iterrows(), 1):
            keywords_found = row.get('Keywords_Found', 'N/A')
            evidence = row.get('Match_Evidence', 'N/A')
           
            print(f"\n[{i}] 행 {idx}")
            print(f"    매칭 키워드: {keywords_found}")
            print(f"    증거: {evidence[:100]}{'...' if len(evidence) > 100 else ''}")
    else:
        print(f"\n⚠️  매칭된 레코드가 없습니다.")
        print(f"   다른 키워드를 시도하거나 임계값을 낮춰보세요.")
 
def print_keyword_statistics(result_df: pd.DataFrame, keywords: list):
    """키워드별 통계 출력"""
    if len(result_df) == 0:
        return
   
    print(f"\n{'='*30}")
    print(f"키워드별 매칭 통계")
    print(f"{'='*30}")
   
    for keyword in keywords:
        count = 0
        for idx, row in result_df.iterrows():
            keywords_found = str(row.get('Keywords_Found', '')).lower()
            if keyword in keywords_found:
                count += 1
       
        percentage = count / len(result_df) * 100 if len(result_df) > 0 else 0
        print(f"{keyword:15} : {count:3}개 ({percentage:5.1f}%)")
 
def main():
    """메인 실행 함수"""
    args = parse_arguments()
   
    # 로깅 설정
    setup_logging(args.verbose)
   
    # 인자 검증
    issues = validate_arguments(args)
    if issues:
        print("❌ 입력 오류:", file=sys.stderr)
        for issue in issues:
            print(f"   - {issue}", file=sys.stderr)
        return 1
   
    try:
        print(f"🔍 키워드 기반 필터링 분석 시작...")
        print(f"   파일: {args.file}")
        print(f"   키워드: {args.keywords}")
        print(f"   유사도 임계값: {args.threshold}")
        print(f"   SBERT 사용: {'예' if args.use_sbert else '아니오'}")
       
        # KeywordBasedMatcher 초기화
        matcher = KeywordBasedMatcher(
            keywords=args.keywords,
            similarity_threshold=args.threshold,
            use_sbert=args.use_sbert,
            alpha=args.alpha
        )
       
        # 분석 실행
        result_df, summary = matcher.analyze_excel(
            file_path=args.file,
            sheet_name=args.sheet,
            output_path=args.output
        )
       
        # 결과 출력
        print_analysis_summary(summary, result_df)
        print_keyword_statistics(result_df, summary['keywords_used'])
       
        # 파일 저장 정보
        if args.output:
            output_file = args.output
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            keywords_str = '_'.join(summary['keywords_used'][:3])
            output_file = f"keyword_analysis_{keywords_str}_{timestamp}.xlsx"
       
        print(f"\n💾 결과가 저장되었습니다: {output_file}")
        print(f"   📊 Analysis_Results 시트: 필터링된 데이터 및 매칭 정보")
        print(f"   ⚙️  Analysis_Settings 시트: 분석 설정 및 매개변수")
        print(f"   📈 Keyword_Statistics 시트: 키워드별 매칭 통계")
       
        # 추가 안내
        if len(result_df) > 0:
            print(f"\n💡 추가 분석을 위한 제안:")
            print(f"   - SBERT 의미 분석을 원하면 --use-sbert 옵션 추가")
            print(f"   - 더 엄격한 필터링을 원하면 --threshold 값 증가 (현재: {args.threshold})")
            print(f"   - 더 관대한 필터링을 원하면 --threshold 값 감소")
        else:
            print(f"\n💡 매칭 결과 개선을 위한 제안:")
            print(f"   - 임계값을 낮춰보세요: --threshold 0.6 또는 0.5")
            print(f"   - 다른 키워드를 시도해보세요")
            print(f"   - 키워드를 더 일반적인 용어로 변경해보세요")
       
        return 0
       
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
 
if __name__ == '__main__':
    sys.exit(main())