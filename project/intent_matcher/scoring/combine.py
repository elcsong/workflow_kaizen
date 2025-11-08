"""
룰 점수와 의미 점수를 결합하는 모듈
최종 판별 점수 계산 및 의사결정
"""
from typing import Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from .rules import RuleScoreComponents
from ..semantics.sbert import SemanticScore
 
@dataclass
class CombinedScore:
    """결합된 최종 점수"""
    rule_score: float
    semantic_score: float
    final_score: float
    alpha: float  # 룰 점수 가중치
    details: Dict[str, Any]
 
@dataclass
class ThresholdConfig:
    """임계값 설정 구성"""
    min_score: Optional[float] = None
    review_band: Optional[Tuple[float, float]] = None
    require_symptom: Optional[bool] = None
    alpha: Optional[float] = None
   
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (None이 아닌 값만)"""
        result = {}
        if self.min_score is not None:
            result['min_score'] = self.min_score
        if self.review_band is not None:
            result['review_band'] = self.review_band
        if self.require_symptom is not None:
            result['require_symptom'] = self.require_symptom
        if self.alpha is not None:
            result['alpha'] = self.alpha
        return result
   
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThresholdConfig':
        """딕셔너리에서 생성"""
        return cls(
            min_score=data.get('min_score'),
            review_band=data.get('review_band'),
            require_symptom=data.get('require_symptom'),
            alpha=data.get('alpha')
        )
 
@dataclass
class MatchResult:
    """최종 매칭 결과"""
    same_defect: str  # 'True', 'False', 'Review'
    confidence: float
    final_score: float
    rule_components: RuleScoreComponents
    semantic_components: SemanticScore
    combined_score: CombinedScore
    evidence: Dict[str, Any]
    reasoning: str
 
class ScoreCombiner:
    """점수 결합 및 최종 판별 클래스"""
   
    def __init__(self, alpha: float = 0.5, threshold_config: Optional[ThresholdConfig] = None):
        """
        Args:
            alpha: 룰 점수의 가중치 (0~1), 1-alpha는 의미 점수 가중치
            threshold_config: 임계값 설정 (선택사항)
        """
        self.alpha = alpha
        self.threshold_config = threshold_config or ThresholdConfig()
       
        # 기본 임계값들 (설정에서 오버라이드 가능)
        self._default_min_score = 0.6
        self._default_review_band = (0.55, 0.60)
        self._default_require_symptom = True
   
    def combine_scores(self, rule_score: float, semantic_score: float) -> CombinedScore:
        """룰 점수와 의미 점수를 결합"""
        import logging
        
        # 가중 평균으로 결합
        final_score = self.alpha * rule_score + (1 - self.alpha) * semantic_score
       
        details = {
            'rule_weight': self.alpha,
            'semantic_weight': 1 - self.alpha,
            'weighted_rule_contribution': self.alpha * rule_score,
            'weighted_semantic_contribution': (1 - self.alpha) * semantic_score
        }
        
        # 디버깅: 점수 결합 과정 로그
        logging.info(f"[Score Combine] rule_score: {rule_score:.3f}, semantic_score: {semantic_score:.3f}")
        logging.info(f"[Score Combine] alpha: {self.alpha} (Rule weight: {self.alpha}, Semantic weight: {1-self.alpha})")
        logging.info(f"[Score Combine] Rule contribution: {self.alpha * rule_score:.3f}")
        logging.info(f"[Score Combine] Semantic contribution: {(1-self.alpha) * semantic_score:.3f}")
        logging.info(f"[Score Combine] FINAL combined score: {final_score:.3f}")
       
        return CombinedScore(
            rule_score=rule_score,
            semantic_score=semantic_score,
            final_score=final_score,
            alpha=self.alpha,
            details=details
        )
   
    def update_thresholds(self, **kwargs) -> None:
        """임계값을 실시간으로 업데이트
       
        Args:
            min_score: 최소 임계점
            review_band: 리뷰 구간 (tuple)
            require_symptom: 증상 필수 여부
            alpha: 룰 vs 의미 점수 가중치
        """
        if 'min_score' in kwargs:
            self.threshold_config.min_score = kwargs['min_score']
        if 'review_band' in kwargs:
            self.threshold_config.review_band = tuple(kwargs['review_band'])
        if 'require_symptom' in kwargs:
            self.threshold_config.require_symptom = kwargs['require_symptom']
        if 'alpha' in kwargs:
            self.threshold_config.alpha = kwargs['alpha']
            self.alpha = kwargs['alpha']
   
    def get_effective_thresholds(self,
                               min_score: Optional[float] = None,
                               review_band: Optional[Tuple[float, float]] = None,
                               require_symptom: Optional[bool] = None) -> Dict[str, Any]:
        """현재 유효한 임계값들을 반환
       
        우선순위: 메서드 매개변수 > 인스턴스 설정 > 기본값
        """
        effective = {}
       
        # min_score 결정
        effective['min_score'] = (
            min_score if min_score is not None
            else self.threshold_config.min_score if self.threshold_config.min_score is not None
            else self._default_min_score
        )
       
        # review_band 결정
        effective['review_band'] = (
            review_band if review_band is not None
            else self.threshold_config.review_band if self.threshold_config.review_band is not None
            else self._default_review_band
        )
       
        # require_symptom 결정
        effective['require_symptom'] = (
            require_symptom if require_symptom is not None
            else self.threshold_config.require_symptom if self.threshold_config.require_symptom is not None
            else self._default_require_symptom
        )
       
        return effective
   
    def make_decision(self, combined_score: CombinedScore,
                     min_score: Optional[float] = None,
                     review_band: Optional[Tuple[float, float]] = None,
                     require_symptom: Optional[bool] = None,
                     rule_components: RuleScoreComponents = None) -> tuple:
        """
        최종 의사결정 수행
       
        Args:
            combined_score: 결합된 점수
            min_score: 최소 임계점 (None이면 설정된 값 사용)
            review_band: 리뷰 구간 (None이면 설정된 값 사용)
            require_symptom: 증상 필수 여부 (None이면 설정된 값 사용)
            rule_components: 룰 점수 세부사항
       
        Returns:
            (decision, confidence, reasoning)
        """
        # 유효한 임계값들 가져오기
        thresholds = self.get_effective_thresholds(min_score, review_band, require_symptom)
        effective_min_score = thresholds['min_score']
        effective_review_band = thresholds['review_band']
        effective_require_symptom = thresholds['require_symptom']
       
        score = combined_score.final_score
        rule_score = rule_components.final_score if rule_components else 0.0
        semantic_score_value = combined_score.semantic_score
       
        # 증상 필수 조건 확인
        if effective_require_symptom and rule_components and rule_components.symptom_score == 0.0:
            reasoning = f'필수 증상이 발견되지 않음 (require_symptom={effective_require_symptom})'
            return 'False', 0.9, reasoning
       
        # 점수 기반 의사결정
        if score >= effective_min_score:
            confidence = min(0.95, 0.6 + (score - effective_min_score) * 0.5)
            reasoning = f'점수 {score:.3f}가 임계값 {effective_min_score} 이상'
            return 'True', confidence, reasoning
       
        elif effective_review_band[0] <= score < effective_review_band[1]:
            confidence = 0.5
            reasoning = f'점수 {score:.3f}가 리뷰 구간 [{effective_review_band[0]}, {effective_review_band[1]}) 내'
            return 'Review', confidence, reasoning
       
        # 특별 케이스: RuleScore=0이지만 SemanticScore가 의미있게 높으면 Review
        # (키워드 매칭 없이 의미만으로 유사도가 높은 경우 → 사람이 검토 필요)
        elif (rule_score == 0.0 and 
              semantic_score_value >= effective_review_band[0]):
            confidence = 0.5
            reasoning = (f'RuleScore는 0이지만 SemanticScore {semantic_score_value:.3f}가 '
                        f'유의미함 (>={effective_review_band[0]}) - 키워드 없이 의미적 유사성만 있음, 검토 필요')
            return 'Review', confidence, reasoning
       
        else:
            confidence = min(0.95, 0.9 - score * 0.5)
            reasoning = f'점수 {score:.3f}가 임계값 {effective_min_score} 미만'
            return 'False', confidence, reasoning
   
    def analyze_record(self,
                      rule_components: RuleScoreComponents,
                      semantic_score: SemanticScore,
                      min_score: Optional[float] = None,
                      review_band: Optional[Tuple[float, float]] = None,
                      require_symptom: Optional[bool] = None,
                      evidence: Dict[str, Any] = None) -> MatchResult:
        """
        레코드에 대한 전체 분석 수행
       
        Args:
            rule_components: 룰 점수 구성요소
            semantic_score: 의미 점수
            min_score: 최소 임계점 (None이면 설정된 값 사용)
            review_band: 리뷰 구간 (None이면 설정된 값 사용)
            require_symptom: 증상 필수 여부 (None이면 설정된 값 사용)
            evidence: 증거 정보
        """
        # 점수 결합
        combined_score = self.combine_scores(
            rule_components.final_score,
            semantic_score.final_score
        )
       
        # 의사결정
        decision, confidence, reasoning = self.make_decision(
            combined_score, min_score, review_band, require_symptom, rule_components
        )
       
        # 증거 정보 보완
        if evidence is None:
            evidence = {}
       
        evidence.update({
            'rule_details': rule_components.details,
            'semantic_details': semantic_score.details,
            'score_breakdown': {
                'symptom_score': rule_components.symptom_score,
                'component_score': rule_components.component_score,
                'negation_penalty': rule_components.negation_penalty,
                'semantic_similarity': semantic_score.similarity_score,
                'contrast_score': semantic_score.contrast_score
            }
        })
       
        return MatchResult(
            same_defect=decision,
            confidence=confidence,
            final_score=combined_score.final_score,
            rule_components=rule_components,
            semantic_components=semantic_score,
            combined_score=combined_score,
            evidence=evidence,
            reasoning=reasoning
        )
   
    def batch_analyze(self,
                     records: list,
                     rule_scores: list,
                     semantic_scores: list,
                     **kwargs) -> list:
        """여러 레코드를 배치로 분석"""
        results = []
       
        for i, (record, rule_comp, sem_score) in enumerate(zip(records, rule_scores, semantic_scores)):
            try:
                result = self.analyze_record(rule_comp, sem_score, **kwargs)
                results.append(result)
            except Exception as e:
                # 에러 발생 시 기본값으로 처리
                error_result = MatchResult(
                    same_defect='Review',
                    confidence=0.0,
                    final_score=0.0,
                    rule_components=rule_comp,
                    semantic_components=sem_score,
                    combined_score=CombinedScore(0.0, 0.0, 0.0, self.alpha, {'error': str(e)}),
                    evidence={'error': str(e)},
                    reasoning=f'분석 중 오류 발생: {str(e)}'
                )
                results.append(error_result)
       
        return results
   
    def get_summary_stats(self, results: list) -> Dict[str, Any]:
        """분석 결과 요약 통계"""
        if not results:
            return {}
       
        decisions = [r.same_defect for r in results]
        scores = [r.final_score for r in results]
        confidences = [r.confidence for r in results]
       
        return {
            'total_records': len(results),
            'true_count': decisions.count('True'),
            'false_count': decisions.count('False'),
            'review_count': decisions.count('Review'),
            'avg_score': sum(scores) / len(scores),
            'avg_confidence': sum(confidences) / len(confidences),
            'score_distribution': {
                'min': min(scores),
                'max': max(scores),
                'median': sorted(scores)[len(scores)//2]
            },
            'threshold_settings': self.get_current_settings()
        }
   
    def get_current_settings(self) -> Dict[str, Any]:
        """현재 임계값 설정 상태 반환"""
        effective = self.get_effective_thresholds()
        return {
            'effective_settings': effective,
            'configured_overrides': self.threshold_config.to_dict(),
            'default_values': {
                'min_score': self._default_min_score,
                'review_band': self._default_review_band,
                'require_symptom': self._default_require_symptom,
                'alpha': self.alpha
            }
        }
   
    def reset_thresholds(self) -> None:
        """임계값을 기본값으로 리셋"""
        self.threshold_config = ThresholdConfig()