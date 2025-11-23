import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer, InputExample, losses
    from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
    from torch.utils.data import DataLoader
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logging.warning("SBERT fine-tuning disabled due to missing dependencies")

class SBERTFineTuner:
    """
    SBERT 파인튜닝 모델 (확장 기능)
    내부 데이터셋을 활용한 대조 학습 및 도메인 적용
    """
    def __init__(self, base_model_name: str = 'all-MiniLM-L6-v2'):
        """
        Args:
            base_model_name: 베이스 SBERT 모델명
        """
        self.base_model_name = base_model_name
        self.model = None
        self.enabled = SBERT_AVAILABLE

        if not self.enabled:
            logging.warning("SBERT fine-tuning disabled due to missing dependencies")


    def define_train_data(self,
                          positive_pairs: List[Tuple[str, str]],
                          negative_pairs: List[Tuple[str, str]],
                          hard_negatives: List[Tuple[str, str]] = None) -> List[InputExample]:
        """
        훈련 데이터 준비

        Args:
            positive_pairs: 유사한 텍스트 쌍들 (동일 불량 유형)
            negative_pairs: 다른 텍스트 쌍들 (다른 불량 유형)
            hard_negatives: 어려운 네거티브 쌍들 (혼동하기 쉬운 것들)
        """
        if not self.enabled:
            return []

        examples = []
        
        # 포지티브 쌍들 (유사도 1.0)
        for text1, text2 in positive_pairs:
            examples.append(InputExample(texts=[text1, text2], label=1.0))

        # 네거티브 쌍들 (유사도 0.0)
        for text1, text2 in negative_pairs:
            examples.append(InputExample(texts=[text1, text2], label=0.0))

        # 하드 네거티브들 (유사도 0.1 - 약간의 유사성은 있지만 다른 유형)
        if hard_negatives:
            for text1, text2 in hard_negatives:
                examples.append(InputExample(texts=[text1, text2], label=0.1))

        logging.info(f"Prepared {len(examples)} training examples")
        return examples

    
    def create_evaluation_data(self,
                               eval_pairs: List[Tuple[str, str, float]]) -> Optional[EmbeddingSimilarityEvaluator]:
        """
        평가 데이터 생성

        Args:
            eval_pairs: (text1, text2, similarity_score) 튜플들
        """
        if not self.enabled or not eval_pairs:
            return None

        sentences1, sentences2, scores = zip(*eval_pairs)
        
        evaluator = EmbeddingSimilarityEvaluator(
            sentences1=list(sentences1),
            sentences2=list(sentences2),
            scores=list(scores),
            name='defect_similarity_eval'
        )
        return evaluator


    def fine_tune(self,
                  training_examples: List[InputExample],
                  evaluator: EmbeddingSimilarityEvaluator = None,
                  output_path: str = './fine_tuned_sbert',
                  epochs: int = 4,
                  batch_size: int = 16,
                  warmup_steps: int = None) -> bool:
        """
        모델 파인튜닝 실행

        Args:
            training_examples: 훈련 예제들
            evaluator: 평가기 (선택사항)
            output_path: 훈련 모델 저장 경로
            epochs: 훈련 에폭 수
            batch_size: 훈련 배치 크기
            warmup_steps: 워밍업 스텝 수
        """
        if not self.enabled or not training_examples:
            logging.error("Cannot fine-tune: SBERT not available or no training data")
            return False

        try:
            # 베이스 모델 로드
            self.model = SentenceTransformer(self.base_model_name)

            # 데이터로더 생성
            train_dataloader = DataLoader(training_examples, shuffle=True, batch_size=batch_size)

            # 손실 함수 정의 (코사인 유사도 손실)
            train_loss = losses.CosineSimilarityLoss(self.model)

            # 워밍업 스텝 계산
            if warmup_steps is None:
                warmup_steps = int(len(train_dataloader) * epochs * 0.1)

            # 파인튜닝 실행
            self.model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                evaluator=evaluator,
                epochs=epochs,
                warmup_steps=warmup_steps,
                output_path=output_path,
                evaluation_steps=len(train_dataloader) // 2, # 에폭 중간에 평가
                save_best_model=True
            )

            logging.info(f"Fine-tuning completed. Model saved to: {output_path}")
            return True

        except Exception as e:
            logging.error(f"Fine-tuning failed: {e}")
            return False
            

    def load_fine_tuned_model(self, model_path: str) -> bool:
        """파인튜닝된 모델 로드"""
        if not self.enabled:
            return False
        
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                logging.error(f"Model path not found: {model_path}")
                return False

            self.model = SentenceTransformer(str(model_path))
            logging.info(f"Fine-tuned model loaded from: {model_path}")
            return True
        
        except Exception as e:
            logging.error(f"Failed to load fine-tuned model: {e}")
            return False


def generate_weak_labels(records: List[Dict[str, str]],
                         target_keywords: List[str],
                         confuser_keywords: List[str]) -> List[Tuple[str, str, float]]:
    """
    약한 라벨 생성 (키워드 기반)

    Args:
        records: 텍스트 레코드들
        target_keywords: 타겟 불량 키워드들
        confuser_keywords: 혼동 불량 키워드들

    Returns:
        (text1, text2, similarity_score) 튜플들
    """
    weak_labels = []

    # 레코드들을 키워드 매칭으로 분류
    target_records = []
    confuser_records = []

    for record in records:
        # 레코드의 모든 텍스트 값들을 결합하여 소문자로 변환
        combined_text = " ".join([text for text in record.values() if text])
        combined_lower = combined_text.lower()

        # 키워드 포함 여부 확인
        has_target = any(keyword.lower() in combined_lower for keyword in target_keywords)
        has_confuser = any(keyword.lower() in combined_lower for keyword in confuser_keywords)

        if has_target and not has_confuser:
            target_records.append(combined_text)
        elif has_confuser and not has_target:
            confuser_records.append(combined_text)

    # 타겟 레코드들 간의 포지티브 쌍 생성 (유사도 0.8)
    for i in range(len(target_records)):
        # 각 레코드당 최대 2개 쌍
        for j in range(i + 1, min(i + 3, len(target_records))): 
             weak_labels.append((target_records[i], target_records[j], 0.8))

    # 타겟 vs 혼동 네거티브 쌍 생성 (유사도 0.1)
    # 상위 10개 타겟, 상위 5개 혼동 레코드만 사용
    for target_text in target_records[:10]: 
        for confuser_text in confuser_records[:5]: 
            weak_labels.append((target_text, confuser_text, 0.1))

    logging.info(f"Generated {len(weak_labels)} weak labels")
    return weak_labels