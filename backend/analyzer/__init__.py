# analyzer
"""AI 分析模块"""

from .scoring import (
    OpportunityScoringEngine,
    OpportunityScore,
    analyze_product_opportunity,
)

__all__ = [
    'OpportunityScoringEngine',
    'OpportunityScore',
    'analyze_product_opportunity',
]
