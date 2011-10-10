from itertools import chain

from oscar.apps.promotions.models import PagePromotion, KeywordPromotion


def promotions(request):
    """
    For adding bindings for banners and pods to the template
    context.
    """
    promotions = PagePromotion._default_manager.select_related() \
                                                .filter(page_url=request.path) \
                                                .order_by('display_order')

    if 'q' in request.GET:
        keyword_promotions = KeywordPromotion._default_manager.select_related().filter(keyword=request.GET['q'])
        if keyword_promotions.count() > 0:
            promotions = list(chain(promotions, keyword_promotions))

    context = {
        'url_path': request.path
    }

    # Split the promotions into separate lists for each position, and 
    # add them to the template bindings
    _split_by_position(promotions, context)

    return context

def _split_by_position(linked_promotions, context):
    """
    Split the list of promotions into separate lists, grouping
    by position, and write these lists to the context dict.
    """
    for linked_promotion in linked_promotions:
        promotion = linked_promotion.content_object
        if not promotion:
            continue
        key = 'promotions_%s' % linked_promotion.position.lower()
        if key not in context:
            context[key] = []
        context[key].append(promotion)
      


        
    
