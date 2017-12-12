from itertools import chain

from oscar.core.loading import get_model

KeywordPromotion = get_model('promotions', 'KeywordPromotion')
PagePromotion = get_model('promotions', 'PagePromotion')


def promotions(request):
    """
    For adding bindings for banners and pods to the template
    context.
    """
    promotions = get_request_promotions(request)

    # Split the promotions into separate lists for each position, and add them
    # to the template bindings
    context = {
        'url_path': request.path
    }
    split_by_position(promotions, context)

    return context


def get_request_promotions(request):
    """
    Return promotions relevant to this request
    """
    promotions = PagePromotion._default_manager.select_related() \
        .prefetch_related('content_object') \
        .filter(page_url=request.path) \
        .order_by('display_order')

    if 'q' in request.GET:
        keyword_promotions \
            = KeywordPromotion._default_manager.select_related()\
            .filter(keyword=request.GET['q'])
        if keyword_promotions.exists():
            promotions = list(chain(promotions, keyword_promotions))
    return promotions


def split_by_position(linked_promotions, context):
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
