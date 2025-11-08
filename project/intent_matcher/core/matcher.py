"""
메인 DefectMatcher 클래스
전체 불량 유형 판별 프로세스를 통합 관리
"""
import pandas as pd
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from pathlib import Path

from .config import TargetConfig
from ..extract.keywords import KeywordExtractor
from ..extract.negation import NegationDetector
from ..semantics.sbert import SBERTAnalyzer, SemanticScore
from ..scoring.rules import RuleScorer
from ..scoring.combine import ScoreCombiner, MatchResult, ThresholdConfig
from ..scoring.policy import PolicyManager
from ..codes.align import CodeAligner


class DefectMatcher:
    """불량 유형 판별 메인 클래스"""
    
    def __init__(self, target_config_path: str, use_sbert: bool = True, alpha: float = 0.5,
                 min_score: Optional[float] = None,
                 review_band: Optional[Tuple[float, float]] = None,
                 require_symptom: Optional[bool] = None,
                 treat_resolved_as_match: Optional[bool] = None):
        """
        Args:
            target_config_path: 타겟 불량 설정 YAML 파일 경로
            use_sbert: SBERT 사용 여부
            alpha: 룰 vs 의미 점수 가중치 (0~1)
            min_score: 최소 임계점 (None이면 설정 파일 사용)
            review_band: 리뷰 구간 (None이면 설정 파일 사용)
            require_symptom: 증상 필수 여부 (None이면 설정 파일 사용)
            treat_resolved_as_match: 해결된 케이스 매칭 여부 (None이면 설정 파일 사용)
        """
        # 설정 로드
        self.config = TargetConfig(target_config_path)
        self.use_sbert = use_sbert
        
        # 임계값 설정 저장
        self.threshold_overrides = {
            'min_score': min_score,
            'review_band': review_band,
            'require_symptom': require_symptom,
            'treat_resolved_as_match': treat_resolved_as_match
        }
        
        # 컴포넌트 초기화
        self.keyword_extractor = KeywordExtractor()
        self.negation_detector = NegationDetector()
        self.rule_scorer = RuleScorer()
        self.policy_manager = PolicyManager(self.config)
        
        # 정책 매니저에 임계값 오버라이드 적용
        cli_args = {k: v for k, v in self.threshold_overrides.items() if v is not None}
        if cli_args:
            self.policy_manager.load_from_cli_args(cli_args)
        
        # ThresholdConfig 생성
        threshold_config = ThresholdConfig(
            min_score=min_score,
            review_band=review_band,
            require_symptom=require_symptom,
            alpha=alpha
        )
        
        # 점수 결합기 초기화 (임계값 설정 포함)
        self.score_combiner = ScoreCombiner(alpha=alpha, threshold_config=threshold_config)
        self.code_aligner = CodeAligner()  # stub으로 비활성화
        
        # SBERT 초기화
        self.sbert_analyzer = None
        if use_sbert:
            self.sbert_analyzer = SBERTAnalyzer()
            if not self.sbert_analyzer.is_available():
                logging.warning("SBERT not available, falling back to rule-only mode")
                self.use_sbert = False
        
        # 타겟 프로토타입 생성 (SBERT용)
        self.target_prototypes = []
        self.confuser_prototypes = []
        if self.use_sbert and self.sbert_analyzer:
            self.target_prototypes = self.sbert_analyzer.create_target_prototypes(
                self.config.name,
                self.config.all_symptoms,
                self.config.action_hints,
                self.config.component_hints
            )
            
            # 혼동 프로토타입 생성
            for confuser in self.config.confusers:
                self.confuser_prototypes.append(f"Issue with {confuser}")
        
        logging.info(f"DefectMatcher initialized for target: {self.config.name}")
        logging.info(f"SBERT enabled: {self.use_sbert}")
    
    def analyze_record(self, record: Dict[str, str],
                      min_score: Optional[float] = None,
                      review_band: Optional[Tuple[float, float]] = None,
                      require_symptom: Optional[bool] = None,
                      treat_resolved_as_match: Optional[bool] = None) -> MatchResult:
        """단일 레코드 분석"""
        try:
            # 1. 룰 기반 점수 계산
            rule_components = self.rule_scorer.calculate_rule_score(
                record_texts=record,
                symptoms=self.config.all_symptoms,
                action_hints=self.config.action_hints,
                component_hints=self.config.component_hints,
                negation_patterns=self.config.negation_patterns,
                require_symptom=self.config.require_symptom,
                treat_resolved_as_match=self.config.treat_resolved_as_match
            )
            
            # 2. 의미 기반 점수 계산
            if self.use_sbert and self.sbert_analyzer:
                semantic_score = self.sbert_analyzer.analyze_record_semantics(
                    record_texts=record,
                    target_prototypes=self.target_prototypes,
                    confuser_prototypes=self.confuser_prototypes,
                    field_weights=self.policy_manager.settings.field_weights
                )
            else:
                semantic_score = SemanticScore(0.0, 0.0, 0.0, {})
            
            # 3. 증거 수집
            evidence = self.rule_scorer.get_evidence_spans(
                record_texts=record,
                symptoms=self.config.all_symptoms,
                action_hints=self.config.action_hints,
                component_hints=self.config.component_hints,
                negation_patterns=self.config.negation_patterns
            )
            
            # 4. 최종 분석 (메서드 매개변수 우선 사용)
            result = self.score_combiner.analyze_record(
                rule_components=rule_components,
                semantic_score=semantic_score,
                min_score=min_score,  # 메서드 매개변수 사용 (None이면 내부에서 설정값 사용)
                review_band=review_band,  # 메서드 매개변수 사용
                require_symptom=require_symptom,  # 메서드 매개변수 사용
                evidence=evidence
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error analyzing record: {e}")
            # 에러 시 기본 결과 반환
            return MatchResult(
                same_defect='Review',
                confidence=0.0,
                final_score=0.0,
                rule_components=None,
                semantic_components=None,
                combined_score=None,
                evidence={'error': str(e)},
                reasoning=f'분석 중 오류 발생: {str(e)}'
            )
    
    def analyze_dataframe(self, df: pd.DataFrame, 
                         text_columns: List[str],
                         id_column: str = None,
                         min_score: Optional[float] = None,
                         review_band: Optional[Tuple[float, float]] = None,
                         require_symptom: Optional[bool] = None,
                         treat_resolved_as_match: Optional[bool] = None) -> pd.DataFrame:
        """
        DataFrame 전체 분석
        
        Args:
            df: 분석할 DataFrame
            text_columns: 텍스트 컬럼명들 (순서: Customers, FE, Actions, Test)
            id_column: ID 컬럼명 (선택사항)
            min_score: 최소 임계점 (메서드 레벨 오버라이드)
            review_band: 리뷰 구간 (메서드 레벨 오버라이드)
            require_symptom: 증상 필수 여부 (메서드 레벨 오버라이드)
            treat_resolved_as_match: 해결된 케이스 매칭 여부 (메서드 레벨 오버라이드)
        """
        results = []
        
        # 컬럼명 매핑
        field_names = ['Customers', 'FE', 'Actions', 'Test']
        column_mapping = {}
        for i, col in enumerate(text_columns):
            if i < len(field_names):
                column_mapping[field_names[i]] = col
        
        # 각 행 분석
        for idx, row in df.iterrows():
            # 레코드 구성
            record = {}
            for field_name, col_name in column_mapping.items():
                record[field_name] = str(row[col_name]) if pd.notna(row[col_name]) else ""
            
            # 분석 실행 (임계값 매개변수 전달)
            result = self.analyze_record(record, min_score=min_score, review_band=review_band,
                                       require_symptom=require_symptom, 
                                       treat_resolved_as_match=treat_resolved_as_match)
            
            # 결과 딕셔너리 구성
            result_dict = {
                'SameDefect': result.same_defect,
                'FinalScore': round(result.final_score, 4),
                'Confidence': round(result.confidence, 4),
                'RuleScore': round(result.rule_components.final_score, 4) if result.rule_components else 0.0,
                'SemanticScore': round(result.semantic_components.final_score, 4) if result.semantic_components else 0.0,
                'Reasoning': result.reasoning,
                'SymptomEvidence': '; '.join(result.evidence.get('symptoms', [])),
                'ActionEvidence': '; '.join(result.evidence.get('actions', [])),
                'NegationEvidence': '; '.join(result.evidence.get('negations', []))
            }
            
            # ID 컬럼이 있으면 추가
            if id_column and id_column in df.columns:
                result_dict['ID'] = row[id_column]
            
            results.append(result_dict)
        
        # 결과 DataFrame 생성
        result_df = pd.DataFrame(results)
        
        # ID 컬럼이 있으면 맨 앞으로 이동
        if id_column and 'ID' in result_df.columns:
            cols = ['ID'] + [col for col in result_df.columns if col != 'ID']
            result_df = result_df[cols]
        
        return result_df
    
    def analyze_excel(self, file_path: str, 
                     sheet_name: str = 'Sheet1',
                     text_columns: List[str] = None,
                     id_column: str = None) -> pd.DataFrame:
        """
        Excel 파일 분석
        
        Args:
            file_path: Excel 파일 경로
            sheet_name: 시트명
            text_columns: 텍스트 컬럼명들
            id_column: ID 컬럼명
        """
        # Excel 파일 로드
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 기본 컬럼명 설정
        if text_columns is None:
            # 일반적인 컬럼명들 시도
            possible_columns = [
                ['Customers Issue Description(Full)', "FE's Issue Description(Full)", 
                 'Actions Taken / Repairs(Full)', 'Repair Test / Inspection Data(Full)'],
                ['CustomerDescription', 'FieldEngineerNotes', 'RepairActions', 'TestResults'],
                ['Customers', 'FE', 'Actions', 'Test']
            ]
            
            for cols in possible_columns:
                if all(col in df.columns for col in cols):
                    text_columns = cols
                    break
            
            if text_columns is None:
                raise ValueError(f"Could not find expected text columns in {list(df.columns)}")
        
        # DataFrame 분석
        return self.analyze_dataframe(df, text_columns, id_column)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """설정 요약 정보 반환"""
        return {
            'target_id': self.config.id,
            'target_name': self.config.name,
            'symptoms_count': len(self.config.all_symptoms),
            'action_hints_count': len(self.config.action_hints),
            'component_hints_count': len(self.config.component_hints),
            'confusers_count': len(self.config.confusers),
            'use_sbert': self.use_sbert,
            'policy_settings': self.policy_manager.export_settings()
        }
    
    def validate_setup(self) -> List[str]:
        """설정 검증"""
        issues = []
        
        # 정책 설정 검증
        policy_issues = self.policy_manager.validate_settings()
        issues.extend(policy_issues)
        
        # SBERT 설정 검증
        if self.use_sbert and not self.sbert_analyzer.is_available():
            issues.append("SBERT is enabled but not available")
        
        # 타겟 프로토타입 검증
        if self.use_sbert and not self.target_prototypes:
            issues.append("No target prototypes generated for SBERT")
        
        return issues
