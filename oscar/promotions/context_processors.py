from django.core.exceptions import ObjectDoesNotExist

from oscar.promotions.abstract_models import BANNER, LEFT_POD, RIGHT_POD
from oscar.services import import_module

promotion_models = import_module('promotions.models', ['PagePromotion'])


def promotions(request):
    u"""
    For adding bindings for banners and pods to the template
    context.
    """
    bindings = {
        'url_path': request.path
    }
    try:
        promotions = promotion_models.PagePromotion._default_manager.filter(page_url=request.path)

        # We split the queries into 3 sets based on the position field
        banners, left_pods, right_pods = [], [], []
        for page_promotion in promotions:
            promotion = page_promotion.promotion
            if page_promotion.position == BANNER:
                banners.append(promotion)
            elif page_promotion.position == LEFT_POD:
                left_pods.append(promotion)
            elif page_promotion.position == RIGHT_POD:
                right_pods.append(promotion)
        bindings['banners'] = banners
        bindings['left_pods'] = left_pods
        bindings['right_pods'] = right_pods
    except ObjectDoesNotExist:
        pass

    return bindings

        
    