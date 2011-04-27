"""
Vanilla promotion models
"""
from oscar.apps.promotions.abstract_models import (AbstractPromotion, AbstractPagePromotion, AbstractKeywordPromotion,
                                                   BANNER, LEFT_POD, RIGHT_POD, RAW_HTML, 
                                                   AbstractMerchandisingBlock, AbstractPageMerchandisingBlock, AbstractKeywordMerchandisingBlock)


class Promotion(AbstractPromotion):
    pass


class PagePromotion(AbstractPagePromotion):
    pass


class KeywordPromotion(AbstractKeywordPromotion):
    pass


class MerchandisingBlock(AbstractMerchandisingBlock):
    pass


class PageMerchandisingBlock(AbstractPageMerchandisingBlock):
    pass


class KeywordMerchandisingBlock(AbstractKeywordMerchandisingBlock):
    pass