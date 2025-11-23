#!/usr/bin/env python3
"""
하이브리드 분석 CLI 인터페이스
Target Complaint ID + 키워드 필터링 + 완전한 스코어링 분석
"""
import argparse
import sys
import logging
from pathlib import Path
import pandas as pd
 
# 패키지 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))
 
from intent_matcher.core.hybrid_matcher import HybridMatcher
 
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
        description='하이브리드 의료기기 결함 분석 도구 (Target ID + Keywords + Full Scoring)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 하이브리드 분석
  python hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe"
 
  # SBERT 의미 분석 포함
  python hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "blood,flow" --use-sbert
 
  # 임계값 설정 - 엄격한 기준 (NEW!)
  python hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "freeze,hang" --min-score 0.85 --review-band 0.8,0.85 --require-symptom true
 
  # 임계값 설정 - 관대한 기준 (NEW!)
  python hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "error,issue" --min-score 0.5 --review-band 0.4,0.5 --require-symptom false
 
  # 가중치 조정 (규칙 기반 70%, 의미 분석 30%)
  python hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "battery,power" --alpha 0.7
 
  # 종합 설정 예시 (NEW!)
  python hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "display,screen" --min-score 0.75 --alpha 0.6 --use-sbert --output analysis_results.xlsx
 
분석 과정:
  1. 타겟 ID 행에서 결함 유형 정보 자동 추출
  2. 키워드로 관련 데이터 1차 필터링  
  3. 필터링된 데이터를 타겟 유형과 비교 분석
  4. 완전한 스코어링 (Rule + Semantic + Policy)
  5. 상세 결과 리포트 생성 (5개 시트)
 
결과 해석:
  - SameDefect: True(동일유형)/False(다른유형)/Review(검토필요)
  - FinalScore: 0.0~1.0 (높을수록 유사)
  - Evidence: 판정 근거 및 매칭 키워드
        """
    )
   
    # 필수 인자
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='분석할 Excel 파일 경로'
    )
   
    parser.add_argument(
        '--target-id', '-t',
        required=True,
        help='기준이 되는 Complaint ID (예: COM-21912149)'
    )
   
    parser.add_argument(
        '--keywords', '-k',
        required=False,
        default="",  #기본값 공백
        help='1차 필터링 키워드들 (콤마 구분). SBERT-only(--use-sbert --alpha 0.0)에서는 비워도 됩니다.'
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
        '--threshold',
        type=float,
        default=0.7,
        help='키워드 유사도 임계값 (0.0~1.0, 기본값: 0.7)'
    )
 
    # NEW: exact-only & auto-short-exact 2025-09-11
    parser.add_argument(
        '--exact-only',
        type=str,
        default='',
        help="정확 일치로만 매칭할 약어 목록 (예: 'ga,oor')"
    )
 
    parser.add_argument(
        '--no-auto-short-exact',
        action='store_true',
        help='길이 <= 3 토근의 자동 exact-only 분류 비활성화'
    )
    ###
    parser.add_argument(
        '--use-sbert',
        action='store_true',
        help='SBERT 의미 분석 사용 (더 정확하지만 느림)'
    )
   
    parser.add_argument(
        '--sbert-only', action='store_true',
        help='Shortcut for pure semantic mode: --use-sbert --alpha 0.0 and bypass keyword prefilter'
    )
 
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.5,
        help='룰 vs 의미 점수 가중치 (0~1, 기본값: 0.5)'
    )
   
    # 임계값 설정 인자들 (NEW!)
    parser.add_argument(
        '--min-score',
        type=float,
        help='최소 임계점 (0.0~1.0, 예: 0.8 - 엄격한 기준)'
    )
   
    parser.add_argument(
        '--review-band',
        type=str,
        help='리뷰 구간 "하한,상한" (예: "0.6,0.7" - 이 구간은 인간 검토 필요)'
    )
   
    parser.add_argument(
        '--require-symptom',
        type=lambda x: x.lower() == 'true',
        help='증상 키워드 필수 여부 (true/false, 기본값: true)'
    )
   
    parser.add_argument(
        '--treat-resolved-as-match',
        type=lambda x: x.lower() == 'true',
        help='해결된 케이스를 매칭으로 인정할지 여부 (true/false, 기본값: true)'
    )
 
    parser.add_argument(
        '--component-hints', type=str,
        help='Comma-separated component keywords to override (e.g., "battery,batteries,pack")'
    )
 
    # --- NLP config & stopwords --- 2025-09-11
    parser.add_argument('--nlp-config', type=str, help='Path to nlp_config.yaml (stopwords/allowlist/regex)')
    parser.add_argument('--no-domain-stopwords', action='store_true',
                        help='Disable built-in domain stopwords (use only global/dataset)')
    parser.add_argument('--exclude-keywords', '-e', default='',
                        help='제외할 키워드 구문 (콤마로 구분, 예: "double click,mirror mode")')

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세 로그 출력'
    )
   
    # argparse에 추가
    parser.add_argument('--keep-filter-evidence', action='store_true',
        help='SBERT-only여도 필터 증거(Filter_* 컬럼)를 생성')
 
    return parser.parse_args()
 
def validate_arguments(args):
    """인자 유효성 검증"""
    issues = []
   
    # 파일 존재 확인
    if not Path(args.file).exists():
        issues.append(f"Input file not found: {args.file}")
   
    # 타겟 ID 확인
    if not args.target_id.strip():
        issues.append("Target Complaint ID cannot be empty")
   
    # 키워드 확인
#    if not args.keywords.strip():
#        issues.append("Keywords cannot be empty")
 
    # 키워드 확인 (SBERT-only: 의미100%일 때는 키워드 없어도 허용)
    keywords_empty = (not args.keywords) or (not args.keywords.strip())
    sbert_only = bool(getattr(args, "use_sbert", False)) and float(getattr(args, "alpha", 0.0)) <= 0.0
    if keywords_empty and not sbert_only:
        issues.append("Keywords cannot be empty (TIP: for SBERT-only, set --use-sbert and --alpha 0.0)")
   
    # 임계값 범위 확인
    if not 0.0 <= args.threshold <= 1.0:
        issues.append(f"Threshold must be between 0.0 and 1.0, got {args.threshold}")
   
    # alpha 범위 확인
    if not 0.0 <= args.alpha <= 1.0:
        issues.append(f"Alpha must be between 0.0 and 1.0, got {args.alpha}")
   
    # 임계값 관련 검증 (NEW!)
    if args.min_score is not None and not 0.0 <= args.min_score <= 1.0:
        issues.append(f"Min score must be between 0.0 and 1.0, got {args.min_score}")
   
    if args.review_band is not None:
        try:
            lower, upper = map(float, args.review_band.split(','))
            if lower >= upper:
                issues.append(f"Review band lower bound must be less than upper bound, got {args.review_band}")
            if not (0.0 <= lower <= 1.0 and 0.0 <= upper <= 1.0):
                issues.append(f"Review band values must be between 0.0 and 1.0, got {args.review_band}")
        except ValueError:
            issues.append(f"Review band must be in format 'lower,upper' (e.g., '0.6,0.7'), got {args.review_band}")
   
    return issues
 
def print_analysis_summary(summary: dict, result_df: pd.DataFrame, args):
    """분석 결과 요약 출력"""
    print(f"\n{'='*60}")
    print(f"하이브리드 분석 결과 요약")
    print(f"{'='*60}")
   
    print(f"\n📋 기본 정보:")
    print(f"   타겟 ID: {summary['target_complaint_id']}")
    print(f"   필터 키워드: {', '.join(summary['filter_keywords'])}")
    print(f"   총 레코드: {summary['total_records']:,}개")
    print(f"   필터링된 레코드: {summary['filtered_records']:,}개")
    print(f"   필터링 비율: {summary['filtered_records']/summary['total_records']*100:.1f}%")
   
    if 'target_config' in summary and summary['target_config']:
        config = summary['target_config']
        print(f"\n🎯 타겟 설정 (자동 추출):")
        print(f"   추출된 증상 키워드: {config['symptoms_count']}개")
        print(f"   주요 증상: {', '.join(config['symptoms'][:5])}{'...' if len(config['symptoms']) > 5 else ''}")
        print(f"   최소 점수 임계값: {config['policy']['min_score']}")
   
    if 'same_defect_true' in summary:
        print(f"\n📊 결함 매칭 결과:")
        total = summary['same_defect_true'] + summary['same_defect_false'] + summary['same_defect_review']
        print(f"   동일 유형 (True): {summary['same_defect_true']:,}개 ({summary['same_defect_true']/total*100:.1f}%)")
        print(f"   다른 유형 (False): {summary['same_defect_false']:,}개 ({summary['same_defect_false']/total*100:.1f}%)")
        print(f"   검토 필요 (Review): {summary['same_defect_review']:,}개 ({summary['same_defect_review']/total*100:.1f}%)")
       
        if 'avg_final_score' in summary:
            print(f"\n📈 점수 통계:")
            print(f"   평균 점수: {summary['avg_final_score']:.3f}")
            print(f"   최고 점수: {summary['max_final_score']:.3f}")
            print(f"   최저 점수: {summary['min_final_score']:.3f}")
   
    if len(result_df) > 0:
        print(f"\n{'='*40}")
        print(f"상위 매칭 결과 미리보기")
        print(f"{'='*40}")
       
        # 점수 순으로 정렬해서 상위 5개 표시
        if 'FinalScore' in result_df.columns:
            top_results = result_df.nlargest(5, 'FinalScore')
        else:
            top_results = result_df.head(5)
       
        for i, (idx, row) in enumerate(top_results.iterrows(), 1):
            complaint_id = row.get('Complaint ID', 'N/A')
            same_defect = row.get('SameDefect', 'N/A')
            final_score = row.get('FinalScore', 0)
            keywords_found = row.get('Filter_Keywords_Found', 'N/A')
           
            print(f"\n[{i}] {complaint_id}")
            print(f"    판정: {same_defect} (점수: {final_score:.3f})")
            print(f"    매칭 키워드: {keywords_found}")
           
            # 증거 정보
            if 'SymptomEvidence' in row and row['SymptomEvidence']:
                evidence = str(row['SymptomEvidence'])[:80]
                print(f"    증상 증거: {evidence}{'...' if len(str(row['SymptomEvidence'])) > 80 else ''}")
    else:
        print(f"\n⚠️  필터링 조건에 매칭된 레코드가 없습니다.")
        print(f"   - 다른 키워드를 시도해보세요")
        print(f"   - 임계값을 낮춰보세요 (현재: {args.threshold})")
 
def print_recommendations(summary: dict, args):
    """추가 분석 제안 출력"""
    print(f"\n{'='*40}")
    print(f"추가 분석 제안")
    print(f"{'='*40}")
   
    if summary['filtered_records'] == 0:
        print(f"🔍 필터링 개선 방안:")
        print(f"   - 더 일반적인 키워드 사용: 'error', 'issue', 'problem'")
        print(f"   - 임계값 낮추기: --threshold 0.5 또는 0.6")
        print(f"   - 키워드 추가: 현재 '{args.keywords}'에 관련 용어 추가")
       
    elif summary['filtered_records'] < 10:
        print(f"📈 결과 확장 방안:")
        print(f"   - 더 포괄적인 키워드 추가")
        print(f"   - 임계값 낮추기: --threshold {max(0.5, args.threshold - 0.1)}")
       
    else:
        print(f"✨ 분석 정밀도 향상:")
        if not args.use_sbert:
            print(f"   - SBERT 의미 분석 활용: --use-sbert")
        print(f"   - 가중치 조정: --alpha 0.7 (규칙 기반 강화)")
        print(f"   - 더 엄격한 키워드 매칭: --threshold 0.8")
       
        # 임계값 조정 제안 (NEW!)
        print(f"   - 엄격한 판정 기준: --min-score 0.8 --require-symptom true")
        print(f"   - 관대한 판정 기준: --min-score 0.5 --require-symptom false")
        print(f"   - 리뷰 구간 조정: --review-band 0.6,0.7")
   
    print(f"\n📊 결과 활용:")
    print(f"   - Analysis_Results: 상세 분석 결과")
    print(f"   - Target_Configuration: 자동 추출된 타겟 설정")
    print(f"   - Analysis_Statistics: 결과 통계")
    print(f"   - Keyword_Statistics: 키워드별 매칭 현황")
 
def main():
    """메인 실행 함수"""
    args = parse_arguments()
    # --sbert-only 플래그가 오면 의미 100% 모드로 강제
    if getattr(args, "sbert_only", False):
        args.use_sbert = True
        args.alpha = 0.0
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
        print(f"🚀 하이브리드 분석 시작...")
        print(f"   파일: {args.file}")
        print(f"   타겟 ID: {args.target_id}")
        print(f"   필터 키워드: {args.keywords}")
        print(f"   SBERT 사용: {'예' if args.use_sbert else '아니오'}")
        print(f"   키워드 임계값: {args.threshold}")
        print(f"   분석 가중치: 규칙 {args.alpha:.1f} : 의미 {1-args.alpha:.1f}")
       
        # 임계값 설정 처리 (NEW!)
        threshold_kwargs = {}
       
        if args.min_score is not None:
            threshold_kwargs['min_score'] = args.min_score
       
        if args.review_band is not None:
            try:
                lower, upper = map(float, args.review_band.split(','))
                threshold_kwargs['review_band'] = (lower, upper)
            except ValueError:
                print(f"❌ Review band 형식 오류: {args.review_band}", file=sys.stderr)
                return 1
       
        if args.require_symptom is not None:
            threshold_kwargs['require_symptom'] = args.require_symptom
       
        if args.treat_resolved_as_match is not None:
            threshold_kwargs['treat_resolved_as_match'] = args.treat_resolved_as_match
 
        # 임계값 설정 정보 출력 (NEW!)
        if threshold_kwargs:
            print(f"   📊 판정 임계값 설정:")
            if 'min_score' in threshold_kwargs:
                print(f"      최소 점수: {threshold_kwargs['min_score']} (이상이면 TRUE)")
            if 'review_band' in threshold_kwargs:
                lower, upper = threshold_kwargs['review_band']
                print(f"      리뷰 구간: {lower}~{upper} (인간 검토 필요)")
            if 'require_symptom' in threshold_kwargs:
                print(f"      증상 필수: {'예' if threshold_kwargs['require_symptom'] else '아니오'}")
            if 'treat_resolved_as_match' in threshold_kwargs:
                print(f"      해결된 케이스 인정: {'예' if threshold_kwargs['treat_resolved_as_match'] else '아니오'}")
        else:
            print(f"   📊 판정 임계값: 기본값 사용 (min_score=0.6, review_band=0.55~0.60)")
 
        # SBERT-only 모드 판별 (의미 100% = alpha == 0)
        sbert_only = args.use_sbert and float(args.alpha) <= 0.0
        filter_keywords = (args.keywords if (args.keep_filter_evidence or not sbert_only) else "")
 
        # HybridMatcher 초기화 (임계값 설정 포함)
       
        matcher = HybridMatcher(
            excel_path=args.file,
            target_complaint_id=args.target_id,
            # SBERT-only일 때는 프리필터를 우회하기 위해 빈 키워드 전달
            filter_keywords=args.keywords,
            similarity_threshold=args.threshold,
            use_sbert=args.use_sbert,
            alpha=args.alpha,
            #NEW: pass-through exact-only config 2025-09-11
            exact_only=[kw.strip() for kw in (args.exact_only or '').strip(',') if kw.strip()],
            auto_short_exact=not args.no_auto_short_exact,
            nlp_config_path=args.nlp_config,
            no_domain_stopwords=args.no_domain_stopwords,
            component_hints_override=args.component_hints,
            **threshold_kwargs  # 임계값 설정 추가
        )
       
        # 분석 실행
        result_df, summary = matcher.analyze_excel(
            sheet_name=args.sheet,
            output_path=args.output
        )
       
        # 결과 출력
        # 리포트/콘솔 요약에 필터 모드를 남겨 재현성 확보
        if sbert_only:
            # 리포트/콘솔에 모드 표시(추적성)
            try:
                summary.setdefault("settings_extra", {})["filtering_mode"] = "none (SBERT-only)"
            except Exception:
                pass
        print_analysis_summary(summary, result_df, args)
        print_recommendations(summary, args)
       
        # 파일 저장 정보
        if args.output:
            output_file = args.output
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            keywords_str = '_'.join(args.keywords.split(',')[:2])  # 처음 2개 키워드만
            output_file = f"hybrid_analysis_{args.target_id}_{keywords_str}_{timestamp}.xlsx"
       
        print(f"\n💾 상세 결과가 저장되었습니다: {output_file}")
        print(f"   📋 Analysis_Results: 필터링 + 분석 결과")
        print(f"   ⚙️  Analysis_Settings: 분석 설정 및 매개변수")
        print(f"   🎯 Target_Configuration: 타겟에서 추출된 설정")
        print(f"   📊 Keyword_Statistics: 키워드별 매칭 통계")
        print(f"   📈 Analysis_Statistics: 결함 분류 결과 통계")
        # NEW 2025-09-11
        print(f" 키워드 임계값: {args.threshold}")
        print(f" 분석 가중치: 규칙 {args.alpha:.1f} : 의미 {1-args.alpha:.1f}")
        if args.exact_only or not args.no_auto_short_exact:
            print(" 🔒 Exact-only 약어 적용:", f"명시={args.exact_only or '없음'}, auto_short_exact={not args.no_auto_short_exact}")
        if args.nlp_config:
            print(f" NLP 구성 파일: {args.nlp_config}")
 
       
        return 0
       
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
 
if __name__ == '__main__':
    sys.exit(main())