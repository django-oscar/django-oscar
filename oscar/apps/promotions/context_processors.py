from itertools import chain

from django.core.exceptions import ObjectDoesNotExist

from oscar.apps.promotions.abstract_models import BANNER, LEFT_POD, RIGHT_POD
from oscar.core.loading import import_module
import_module('promotions.models', ['PagePromotion', 'KeywordPromotion', 
                                    'PageMerchandisingBlock', 'KeywordMerchandisingBlock'], locals())


def promotions(request):
    u"""
    For adding bindings for banners and pods to the template
    context.
    """
    bindings = {
        'url_path': request.path
    }
    promotions = PagePromotion._default_manager.select_related().filter(page_url=request.path)

    if 'q' in request.GET:
        keyword_promotions = KeywordPromotion._default_manager.select_related().filter(keyword=request.GET['q'])
        if keyword_promotions.count() > 0:
            promotions = list(chain(promotions, keyword_promotions))

    bindings['banners'], bindings['left_pods'], bindings['right_pods'] = _split_by_position(promotions)

    return bindings

def merchandising_blocks(request):
    bindings = {
        'url_path': request.path
    }
    blocks = PageMerchandisingBlock._default_manager.select_related().filter(page_url=request.path)

    if 'q' in request.GET:
        keyword_blocks = KeywordMerchandisingBlock._default_manager.select_related().filter(keyword=request.GET['q'])
        if keyword_blocks.count() > 0:
            blocks = list(chain(blocks, keyword_blocks))

    bindings['merchandising_blocks'] = blocks

    return bindings


def _split_by_position(linked_promotions):
    # We split the queries into 3 sets based on the position field
    banners, left_pods, right_pods = [], [], []
    for linked_promotion in linked_promotions:
        promotion = linked_promotion.promotion
        if linked_promotion.position == BANNER:
            banners.append(promotion)
        elif linked_promotion.position == LEFT_POD:
            left_pods.append(promotion)
        elif linked_promotion.position == RIGHT_POD:
            right_pods.append(promotion)
        promotion.set_proxy_link(linked_promotion.get_link())    
    return banners, left_pods, right_pods        


        
    