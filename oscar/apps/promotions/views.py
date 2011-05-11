from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from oscar.core.loading import import_module

promotions_models = import_module('promotions.models', ['PagePromotion', 'KeywordPromotion'])


class HomeView(object):
    u"""
    View for the homepage.
    """

    template_file = 'oscar/home.html'

    def __call__(self, request, *args, **kwargs):
        return TemplateResponse(request, self.template_file)


def page_promotion_click(request, page_promotion_id):
    u"""Records a click-through on a promotion"""
    page_prom = get_object_or_404(promotions_models.PagePromotion, id=page_promotion_id)
    if page_prom.promotion.has_link:
        page_prom.record_click()
        return HttpResponseRedirect(page_prom.promotion.link_url)
    return Http404()
    
def keyword_promotion_click(request, keyword_promotion_id):
    u"""Records a click-through on a promotion"""
    keyword_prom = get_object_or_404(promotions_models.KeywordPromotion, id=keyword_promotion_id)
    if keyword_prom.promotion.has_link:
        keyword_prom.record_click()
        return HttpResponseRedirect(keyword_prom.promotion.link_url)
    return Http404()

