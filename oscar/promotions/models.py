"""
Vanilla promotion models
"""
from oscar.promotions.abstract_models import AbstractPromotion, AbstractPagePromotion


class Promotion(AbstractPromotion):
    pass


class PagePromotion(AbstractPagePromotion):
    pass