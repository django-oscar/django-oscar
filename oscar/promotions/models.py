"""
Vanilla promotion models
"""
from oscar.promotions.abstract_models import AbstractPromotion, AbstractPagePromotion, AbstractKeywordPromotion


class Promotion(AbstractPromotion):
    pass


class PagePromotion(AbstractPagePromotion):
    pass


class KeywordPromotion(AbstractKeywordPromotion):
    pass