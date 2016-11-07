from django.conf import settings
from oscar.core.loading import get_model


def get_default_review_status():
    ProductReview = get_model('reviews', 'ProductReview')

    if settings.OSCAR_MODERATE_REVIEWS:
        return ProductReview.FOR_MODERATION

    return ProductReview.APPROVED
