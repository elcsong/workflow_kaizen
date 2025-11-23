import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logging.warning("sentence-transformers not installed. SBERT features will be disabled.")

@dataclass
class SemanticScore:
    """의미 분석 점수 결과"""
    similarity: float  # 유사도 점수
    contrast_score: float  # #vs 혼동 타겟과의 대조 점수
    final_score: float  # = sim_pos - max(sim_confusers)
    details: Dict[str, float]

class SBERTAnalyzer:
    """SBERT 기반 의미 분석기"""
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Args:
            model_name: 사용할 SBERT 모델명
        """
        self.model_name = model_name
        self.model = None
        self.enabled = SBERT_AVAILABLE

        # 로컬 모델 경로 설정 (윈도우 호환)
        local_model_path = Path("models") / model_name  # 예: models/all-MiniLM-L6-v2

        if self.enabled:
            try:
                if local_model_path.exists():
                    # Path 객체를 문자열로 변환 (윈도우 호환)
                    self.model = SentenceTransformer(str(local_model_path))
                    logging.info(f"로컬 SBERT 모델 로드됨: {local_model_path}")
                else:
                    self.model = SentenceTransformer(model_name)
                    logging.info(f"HuggingFace에서 SBERT 모델 로드됨: {model_name}")
            except Exception as e:
                logging.error(f"Failed to load SBERT model: {e}")
                self.enabled = False
        else:
            logging.warning("SBERT analyzer disabled due to missing dependencies")


    def is_available(self) -> bool:
        """SBERT 기능 사용 여부"""
        return self.enabled and self.model is not None

    def encode_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """텍스트들을 임베딩으로 변환"""
        if not self.is_available() or not texts:
            return None
        
        try:
            # 빈 텍스트 처리
            processed_texts = [text if text and text.strip() else "empty" for text in texts]
            embeddings = self.model.encode(processed_texts)
            return embeddings
        except Exception as e:
            logging.error(f"Failed to encode texts ({e})")
            return None


    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 코사인 유사도 계산"""
        if not self.is_available():
            return 0.0

        try:
            embeddings = self.encode_texts([text1, text2])
            if embeddings is None or len(embeddings) != 2:
                return 0.0
            
            # 코사인 유사도 계산
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]) 
            )

            # -1 ~ 1 범위를 0 ~ 1로 변환
            return max(0.0, (similarity + 1) / 2)

        except Exception as e:
            logging.error(f"Failed to calculate similarity: {e}")
            return 0.0


    def calculate_similarity_matrix(self, target_texts: List[str], candidate_texts: List[str]) -> Optional[np.ndarray]:
        """타겟 텍스트들과 후보 텍스트들 간의 유사도 행렬 계산"""
        if not self.is_available() or not target_texts or not candidate_texts:
            return None

        try:
            all_texts = target_texts + candidate_texts
            embeddings = self.encode_texts(all_texts)
            
            if embeddings is None:
                return None

            n_targets = len(target_texts)
            target_embeddings = embeddings[:n_targets]
            candidate_embeddings = embeddings[n_targets:]

            # 유사도 행렬 계산
            similarity_matrix = np.dot(target_embeddings, candidate_embeddings.T)

            # 정규화
            target_norms = np.linalg.norm(target_embeddings, axis=1, keepdims=True)
            candidate_norms = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
            similarity_matrix = similarity_matrix / (target_norms * candidate_norms.T)

            # 0 ~ 1 범위로 변환
            similarity_matrix = np.maximum(0.0, (similarity_matrix + 1) / 2)

            return similarity_matrix

        except Exception as e:
            logging.error(f"Failed to calculate similarity matrix: {e}")
            return None


    def analyze_record_semantics(self, record_texts: Dict[str, str],
                                target_prototypes: List[str],
                                confuser_prototypes: List[str] = None,
                                field_weights: Dict[str, float] = None) -> SemanticScore:
        """
        레코드의 의미론적 분석 수행

        Args:
            record_texts: 필드별 텍스트 딕셔너리
            target_prototypes: 타겟 텍스트의 프로토타입 텍스트들
            confuser_prototypes: 혼동 가능한 불량들의 프로토타입
            field_weights: 필드별 가중치
        """
        if not self.is_available():
            return SemanticScore(0.0, 0.0, 0.0, {})

        try:
            # 기본 가중치 설정
            if field_weights is None:
                field_weights = {
                    'Customers': 0.25,
                    'PE': 0.35,
                    'Actions': 0.25,
                    'Test': 0.15
                }

            # 레코드 텍스트 결합 (가중치 고려)
            combined_texts = []
            field_similarities = {}

            for field_name, text in record_texts.items():
                if not text or not text.strip():
                    continue

                weight = field_weights.get(field_name, 0.1)

                # 각 필드별로 타겟과의 유사도 계산
                field_sims = []
                for prototype in target_prototypes:
                    sim = self.calculate_similarity(text, prototype)
                    field_sims.append(sim)

                max_field_sim = max(field_sims) if field_sims else 0.0
                field_similarities[field_name] = max_field_sim
                
                # 가중치를 적용하여 중요한 필드일수록 더 많이 반복
                repeat_count = max(1, int(weight * 10))
                combined_texts.extend([text] * repeat_count)
            
            if not combined_texts:
                return SemanticScore(0.0, 0.0, 0.0, {})

            # 결합된 텍스트로 전체 유사도 계산
            combined_text = " ".join(combined_texts)

            # 타겟과의 유사도
            target_similarities = []
            for prototype in target_prototypes:
                sim = self.calculate_similarity(combined_text, prototype)
                target_similarities.append(sim)

            max_target_sim = max(target_similarities) if target_similarities else 0.0

            # 혼동 타겟과의 대조 점수
            max_confuser_sim = 0.0
            confuser_similarities = {}

            if confuser_prototypes:
                for i, confuser in enumerate(confuser_prototypes):
                    sim = self.calculate_similarity(combined_text, confuser)
                    confuser_similarities[f'confuser_{i}'] = sim
                    max_confuser_sim = max(max_confuser_sim, sim)
            
            # 대조 점수 계산: sim_pos - max(sim_confusers)
            contrast_score = max(0.0, max_target_sim - max_confuser_sim)

            details = {
                'target_similarity': max_target_sim,
                'max_confuser_similarity': max_confuser_sim,
                'field_similarities': field_similarities,
                'confuser_similarities': confuser_similarities
            }

            return SemanticScore(
                similarity=max_target_sim,
                contrast_score=contrast_score,
                final_score=contrast_score,
                details=details
            )
        
        except Exception as e:
            logging.error(f"Failed to calculate similarity matrix: {e}")
            return SemanticScore(0.0, 0.0, 0.0, {})