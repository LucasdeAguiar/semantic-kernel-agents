import logging
from openai import OpenAI
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ModerationResult:
    """
    Resultado estruturado da moderação.
    """
    def __init__(self, flagged: bool, categories: Dict[str, bool], highest_score: float, provider: str):
        self.flagged = flagged
        self.categories = categories
        self.highest_score = highest_score
        self.provider = provider

    def __repr__(self):
        return f"<ModerationResult flagged={self.flagged} provider={self.provider}>"


class ContentModerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def analisar_mensagem(self, texto: str) -> ModerationResult:
        """
        Analisa uma mensagem de texto quanto a conteúdo inadequado.
        """
        try:
            response = self.client.moderations.create(
                input=texto,
                model="omni-moderation-latest"  
            )

            result = response.results[0]
            highest_score = self._extract_highest_score(result.category_scores)
            categories = self._extract_categories(result.categories)

            return ModerationResult(
                flagged=result.flagged,
                categories=categories,
                highest_score=highest_score,
                provider="openai"
            )
        except Exception as e:
            logger.warning(f"[MODERAÇÃO] Erro ao analisar conteúdo: {e}")
            return ModerationResult(flagged=False, categories={}, highest_score=0.0, provider="openai")

    def _extract_highest_score(self, category_scores) -> float:
        """Extrai o score mais alto das categorias"""
        if not category_scores:
            return 0.0
        
        scores = []
        for attr in dir(category_scores):
            if not attr.startswith('_'):
                try:
                    score_value = getattr(category_scores, attr)
                    if isinstance(score_value, (int, float)):
                        scores.append(score_value)
                except (AttributeError, TypeError):
                    continue
        return max(scores) if scores else 0.0

    def _extract_categories(self, categories) -> Dict[str, bool]:
        """Extrai as categorias de moderação"""
        if hasattr(categories, 'model_dump'):
            return categories.model_dump()
        return dict(categories) if categories else {}
