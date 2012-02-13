from oscar.core.loading import get_classes

SingleProduct, RawHTML, Image, MultiImage, PagePromotion = get_classes('promotions.models',
    ['SingleProduct', 'RawHTML', 'Image', 'MultiImage', 'PagePromotion'])


def get_promotion_classes():
    return (RawHTML, Image, SingleProduct)



PROMOTION_CLASSES = get_promotion_classes()
