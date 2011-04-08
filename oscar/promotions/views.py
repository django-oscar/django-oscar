from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from oscar.services import import_module

promotions_models = import_module('promotions.models', ['PagePromotion'])


def promotion_click(request, page_promotion_id):
    u"""Records a click-through on a promotion"""
    page_prom = get_object_or_404(promotions_models.PagePromotion, id=page_promotion_id)
    if page_prom.promotion.has_link:
        page_prom.record_click()
        return HttpResponseRedirect(page_prom.promotion.link_url)
    return Http404()
    

