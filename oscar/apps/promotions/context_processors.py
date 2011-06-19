from itertools import chain

from django.core.exceptions import ObjectDoesNotExist

from oscar.apps.promotions.models import PagePromotion


def promotions(request):
    """
    For adding bindings for banners and pods to the template
    context.
    """
    context = {
        'url_path': request.path
    }
    # @todo need caching here / and order bt
    promotions = PagePromotion._default_manager.select_related().filter(page_url=request.path)

    if 'q' in request.GET:
        keyword_promotions = KeywordPromotion._default_manager.select_related().filter(keyword=request.GET['q'])
        if keyword_promotions.count() > 0:
            promotions = list(chain(promotions, keyword_promotions))

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
        key = 'promotions_%s' % linked_promotion.position.lower()
        if key not in context:
            context[key] = []
        context[key].append(linked_promotion.content_object)
        linked_promotion.content_object.set_proxy_link(linked_promotion.get_link())
      


        
    